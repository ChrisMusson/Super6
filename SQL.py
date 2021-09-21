import sqlite3

from typing import List

from classes.result import Result
from classes.prediction import Prediction
from classes.user import User


def initialise_database(cursor: sqlite3.Cursor) -> None:
    '''Initialises each table in the final database'''

    cursor.execute('''
        CREATE TABLE Users (
            user_id int,
            first_name text,
            last_name text
        )
    ''')

    cursor.execute('''
        CREATE TABLE Predictions (
            user_id int,
            round_number int,
            challenge_id int,
            home_score int,
            away_score int
        )
    ''')

    cursor.execute('''
        CREATE TABLE Results (
            challenge_id int,
            round_number int,
            home_score int,
            away_score int,
            started int,
            finished int,
            void int
        )
    ''')

    cursor.execute('''
        CREATE TABLE Calculations (
            user_id int,
            name text,
            played int,
            results int,
            scores int,
            points int,
            pts_per_round real,
            variance real,
            off_by_1 int,
            off_by_2 int,
            off_by_3 int,
            off_by_more int
        )
    ''')


def get_last_update(cursor: sqlite3.Cursor) -> dict:
    '''Returns the round number and whether the round was finished when the database was last updated'''

    last_update_round = cursor.execute('''
        SELECT round_number
        FROM Results
        ORDER BY round_number DESC
        LIMIT 1
    ''').fetchone()

    if last_update_round is None:
        last_update_round = 0
        round_finished = False
    else:
        last_update_round = last_update_round[0]

        round_finished = cursor.execute('''
            SELECT *
            FROM Results
            WHERE finished = 0 AND round_number = ?
        ''', (last_update_round,)).fetchone() is None

    return {"round": last_update_round, "finished": round_finished}


def read_ids_from_db(cursor: sqlite3.Cursor) -> List[int]:
    '''Returns a list of user_ids that are currently stored in the Users table'''

    return [x[0] for x in cursor.execute('''
        SELECT user_id
        FROM Users
    ''').fetchall()]


def insert_into_users(cursor: sqlite3.Cursor, users: List[User]) -> None:
    '''Inserts user data from multiple User objects into the Users table'''

    users = [tuple(vars(x).values()) for x in users]
    cursor.executemany('''
        INSERT INTO Users
        VALUES (?, ?, ?)
    ''', users)


def delete_from_users(cursor: sqlite3.Cursor, user_ids: List[int]) -> None:
    '''Deletes user data for multiple user_ids from the Users table'''

    user_ids = [(x,) for x in user_ids]
    cursor.executemany('''
        DELETE FROM Users
        WHERE user_id = ?
    ''', user_ids)


def insert_into_results(cursor: sqlite3.Cursor, results: List[Result]) -> None:
    '''Inserts result data for multiple Result objects into the Results table'''

    results = [tuple(vars(x).values()) for x in results]
    cursor.executemany('''
        INSERT INTO Results
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', results)


def delete_from_results(
        cursor: sqlite3.Cursor,
        round_numbers: List[int] = None,
        challenge_ids: List[int] = None
    ) -> None:
    '''Deletes result data for multiple round_numbers and/or challenge_ids from the Results table'''

    if round_numbers is not None:
        round_numbers = [(x,) for x in round_numbers]
        cursor.executemany('''
            DELETE FROM Results
            WHERE round_number = ?
        ''', round_numbers)

    if challenge_ids is not None:
        challenge_ids = [(x,) for x in challenge_ids]
        cursor.executemany('''
            DELETE FROM Results
            WHERE challenge_id = ?
        ''', challenge_ids)



def insert_into_predictions(cursor: sqlite3.Cursor, predictions: List[Prediction]) -> None:
    '''Inserts prediction data for multiple Prediction objects into the Predictions table'''

    predictions = [tuple(vars(x).values()) for x in predictions]
    cursor.executemany('''
        INSERT INTO Predictions
        VALUES (?, ?, ?, ?, ?)
    ''', predictions)


def delete_from_predictions(cursor: sqlite3.Cursor, user_ids: List[int]) -> None:
    '''Deletes prediction data for multiple user_ids from the Predictions table'''

    user_ids = [(x,) for x in user_ids]
    cursor.executemany('''
        DELETE FROM Predictions
        WHERE user_id = ?
    ''', user_ids)


def off_by(cursor, user_id, x, exactly=True) -> int:
    '''Returns how many predictions were wrong by exactly x goals if exactly=True,
    or at least x goals otherwise'''

    if exactly:
        operator = "="
    else:
        operator = ">="
    
    return cursor.execute(f'''
        SELECT count(*)
        FROM (SELECT * FROM Predictions WHERE user_id = ?) x
        INNER JOIN Results
        ON x.challenge_id = Results.challenge_id
        WHERE abs(x.home_score - Results.home_score) + abs(x.away_score - Results.away_score) {operator} ?
    ''', (user_id, x)).fetchone()[0]


def insert_into_calculations(cursor: sqlite3.Cursor, user_id: int) -> None:
    '''Calculates and populates the Calculations table for a given user_id'''

    user_name = " ".join(cursor.execute('''
        SELECT first_name, last_name
        FROM Users
        WHERE user_id = ?
    ''', (user_id,)).fetchone())

    rounds_played = cursor.execute('''
        SELECT count(*)/6
        FROM Predictions
        WHERE user_id = ?
    ''', (user_id,)).fetchone()[0]

    correct_results = cursor.execute('''
        SELECT count(*)
        FROM (SELECT * FROM Predictions WHERE user_id = ?) x
        INNER JOIN Results
        ON x.challenge_id = Results.challenge_id
        WHERE ((x.home_score - x.away_score > 0 AND  Results.home_score - Results.away_score > 0)
            OR (x.home_score - x.away_score = 0 AND  Results.home_score - Results.away_score = 0)
            OR (x.home_score - x.away_score < 0 AND  Results.home_score - Results.away_score < 0)
            )
            AND (x.home_score != Results.home_score OR x.away_score != Results.away_score)
    ''', (user_id,)).fetchone()[0]

    correct_scores = off_by(cursor, user_id, 0)

    points = correct_scores * 5 + correct_results * 2

    off_by_1 = off_by(cursor, user_id, 1)
    off_by_2 = off_by(cursor, user_id, 2)
    off_by_3 = off_by(cursor, user_id, 3)
    off_by_4_or_more = off_by(cursor, user_id, 4, exactly=False)

    pts_per_round = 0
    if rounds_played > 0:
        pts_per_round = round(points / rounds_played, 2)

    variance = cursor.execute('''
        SELECT ROUND(AVG(round_score*round_score) - AVG(round_score)*AVG(round_score), 2) variance
        FROM(
            SELECT SUM(
                2 * (
                        (
                               (x.home_score - x.away_score > 0 AND  Results.home_score - Results.away_score > 0)
                            OR (x.home_score - x.away_score = 0 AND  Results.home_score - Results.away_score = 0)
                            OR (x.home_score - x.away_score < 0 AND  Results.home_score - Results.away_score < 0)
                        )	
                        AND (x.home_score != Results.home_score OR x.away_score != Results.away_score)
                    )
                + 5 * (abs(x.home_score - Results.home_score) + abs(x.away_score - Results.away_score) = 0)
            ) round_score
                        
            FROM (SELECT * FROM Predictions WHERE user_id = ?) x
            INNER JOIN Results
            ON x.challenge_id = Results.challenge_id
            GROUP BY x.round_number)
    ''', (user_id,)).fetchone()[0]

    cursor.execute('''
        INSERT INTO Calculations
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (user_id, user_name, rounds_played, correct_results, correct_scores, points, pts_per_round,
          variance, off_by_1, off_by_2, off_by_3, off_by_4_or_more))


def delete_from_calculations(cursor: sqlite3.Cursor) -> None:
    '''Removes all records from the Calculations table'''

    cursor.execute('''
        DELETE FROM Calculations
    ''')


def get_calculations(cursor: sqlite3.Cursor, limit: int = 100) -> None:
    '''Returns the top `limit` users from the Calculations table'''

    return cursor.execute('''
        SELECT *
        FROM Calculations
        ORDER BY points DESC, scores DESC
        LIMIT ?
    ''', (limit,))
