import sqlite3
from os import path
from prettytable import PrettyTable
import csv
import aiohttp
import asyncio


async def fetch(session, url):
    async with session.get(url) as resp:
        assert resp.status == 200
        return await resp.json()


def initialise_database(cursor):

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
            match_id int,
            round_number int,
            home int,
            away int
        )
    ''')

    cursor.execute('''
        CREATE TABLE Results (
            match_id int,
            round_number int,
            home int,
            away int
        )
    ''')

    cursor.execute('''
        CREATE TABLE Rounds (
            match_id int,
            round_number int
        )
    ''')

    cursor.execute('''
        CREATE TABLE Calculations (
            user_id int,
            user_name text,
            rounds_played int,
            correct_results int,
            correct_scores int,
            points int,
            pts_per_round real,
            off_by_1 int,
            off_by_2 int,
            off_by_3 int,
            off_by_4_or_more int
        )
    ''')


async def update_users(session, cursor):
    with open("IDs.csv", "r") as f:
        reader = csv.reader(f)
        IDs_from_file = [int(ID.strip()) for ID in next(reader)]

    IDs_from_database = [x[0] for x in
                         cursor.execute('''
            SELECT user_id
            FROM Users
        ''').fetchall()
    ]

    users_to_add = [
        user_id for user_id in IDs_from_file if user_id not in IDs_from_database]

    users_to_delete = [
        user_id for user_id in IDs_from_database if user_id not in IDs_from_file]

    for user_id in users_to_add:
        try:
            user_data = await fetch(session, f"https://super6.skysports.com/api/v2/score/leaderboard/user/{user_id}?period=season")
            first_name, last_name = user_data["firstName"], user_data["lastName"]

            cursor.execute('''INSERT INTO Users VALUES(?, ?, ?)''',
                        (user_id, first_name.capitalize(), last_name.capitalize()))
        except AssertionError:
            print(f"The webpage 'https://super6.skysports.com/api/v2/score/leaderboard/user/{user_id}?period=season' could not be reached. This may be because you are not connected to the internet, or because user_id {user_id} is not a valid ID.")

    for user_id in users_to_delete:
        cursor.execute('''
            DELETE FROM Users 
            WHERE user_id = ?
        ''', (user_id,))

        cursor.execute('''
            DELETE FROM Predictions 
            WHERE user_id = ?
        ''', (user_id,))

        cursor.execute('''
            DELETE FROM Calculations 
            WHERE user_id = ?
        ''', (user_id,))


async def update_single_round_info_and_results(session, cursor, round_number, active_round):
    # Completely ignore round 50 as that was voided with no points awarded due to COVID 19
    if round_number != 50:
        data = await fetch(session, f"https://super6.skysports.com/api/v2/round/{round_number}")
        for match in data["scoreChallenges"]:
            cursor.execute('''
                INSERT INTO Rounds
                VALUES (?, ?)
            ''',
                        (round_number, match["match"]["id"])
                        )
            if round_number != active_round:
                cursor.execute('''
                    INSERT INTO Results
                    VALUES (?, ?, ?, ?)
                ''', (match["match"]["id"], round_number, match["match"]["homeTeam"]["score"], match["match"]["awayTeam"]["score"]))


async def update_multiple_rounds_info_and_results(session, cursor, active_round):
    last_updated_round = cursor.execute('''
        SELECT MAX(round_number)
        FROM Rounds
    ''').fetchone()[0]

    if last_updated_round == None:
        last_updated_round = 0

    if last_updated_round < active_round:
        tasks = []
        for round_number in range(last_updated_round+1, active_round+1):
            tasks.append(update_single_round_info_and_results(
                session, cursor, round_number, active_round))

        return await asyncio.gather(*tasks)


async def update_single_user_single_round_predictions(session, cursor, user_id, round_number):
    # Completely ignore round 50 as that was voided with no points awarded due to COVID 19
    if round_number != 50:
        data = await fetch(session, f"https://super6.skysports.com/api/v2/round/{round_number}/user/{user_id}")
        if data["hasPredicted"]:
            for pred in data["predictions"]["scores"]:
                match_id, home, away = pred["matchId"], pred["scoreHome"], pred["scoreAway"]
                cursor.execute('''INSERT INTO Predictions VALUES(?, ?, ?, ?, ?)''',
                            (user_id, match_id, round_number, home, away))

        else:
            match_ids = [x[0] for x in cursor.execute('''
            SELECT match_id
            FROM Rounds
            WHERE round_number == ?
        ''', (round_number,)).fetchall()]
            for match_id in match_ids:
                cursor.execute('''INSERT INTO Predictions VALUES(?, ?, ?, ?, ?)''',
                            (user_id, match_id, round_number, None, None))


async def update_single_user_multiple_rounds_predictions(session, cursor, user_id, active_round):
    last_updated_round = cursor.execute('''
        SELECT MAX(round_number)
        FROM Predictions
        WHERE user_id = ?
    ''', (user_id,)).fetchone()[0]

    if last_updated_round == None:
        last_updated_round = 0

    if last_updated_round < active_round:
        tasks = []
        # have to add the special case of excluding round 50, as that round was voided due to COVID 19
        for round_number in range(last_updated_round+1, active_round):
            tasks.append(update_single_user_single_round_predictions(
                session, cursor, user_id, round_number))

        return await asyncio.gather(*tasks)


async def update_multiple_users_multiple_rounds_predictions(session, cursor, active_round):
    tasks = []
    for user_id in [x[0] for x in
                    cursor.execute('''
            SELECT user_id
            FROM Users
        ''').fetchall()
                    ]:
        tasks.append(update_single_user_multiple_rounds_predictions(
            session, cursor, user_id, active_round))
    return await asyncio.gather(*tasks)


def off_by(cursor, user_id, x, exactly=True):
    '''returns how many predictions were wrong by exactly x goals if exactly=True,
    at least x goals otherwise'''

    if exactly:
        return cursor.execute('''
            SELECT count(*)
            FROM (SELECT * FROM Predictions WHERE user_id = ?) x
            INNER JOIN Results
            ON x.match_id = Results.match_id
            WHERE abs(x.home - Results.home) + abs(x.away - Results.away) = ?
        ''', (user_id, x)).fetchone()[0]

    else:
        return cursor.execute('''
            SELECT count(*)
            FROM (SELECT * FROM Predictions WHERE user_id = ?) x
            INNER JOIN Results
            ON x.match_id = Results.match_id
            WHERE abs(x.home - Results.home) + abs(x.away - Results.away) >= ?
        ''', (user_id, x)).fetchone()[0]


async def update_single_user_calculations(cursor, user_id):

    user_name = " ".join(cursor.execute('''
        SELECT first_name, last_name
        FROM Users
        WHERE user_id = ?
    ''', (user_id,)).fetchone())

    rounds_played = cursor.execute('''
        SELECT count(*)/6
        FROM (SELECT * FROM Predictions WHERE user_id = ?) x
        WHERE x.home IS NOT NULL
    ''', (user_id,)).fetchone()[0]

    correct_results = cursor.execute('''
        SELECT count(*)
        FROM (SELECT * FROM Predictions WHERE user_id = ?) x
        INNER JOIN Results
        ON x.match_id = Results.match_id
        WHERE ((x.home - x.away > 0 AND  Results.home - Results.away > 0)
            OR (x.home - x.away = 0 AND  Results.home - Results.away = 0)
            OR (x.home - x.away < 0 AND  Results.home - Results.away < 0)
            )
            AND (x.home != Results.home OR x.away != Results.away)
    ''', (user_id,)).fetchone()[0]

    correct_scores = off_by(cursor, user_id, 0)

    points = correct_scores*5 + correct_results*2

    off_by_1 = off_by(cursor, user_id, 1)
    off_by_2 = off_by(cursor, user_id, 2)
    off_by_3 = off_by(cursor, user_id, 3)
    off_by_4_or_more = off_by(cursor, user_id, 4, exactly=False)

    pts_per_round = round(points / rounds_played, 2)

    cursor.execute('''
        INSERT INTO Calculations
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (user_id, user_name, rounds_played, correct_results, correct_scores, points, pts_per_round, off_by_1, off_by_2, off_by_3, off_by_4_or_more))


async def update_multiple_user_calculations(cursor):
    # brutish way to make sure records don't get repeated
    # would be better to check for any changes and if they exist update, else don't
    cursor.execute('''
        DELETE FROM Calculations
    ''')

    tasks = []
    for user_id in [x[0] for x in
                    cursor.execute('''
            SELECT user_id
            FROM Users
        ''').fetchall()
                    ]:
        tasks.append(update_single_user_calculations(
            cursor, user_id))
    return await asyncio.gather(*tasks)

def print_final_table(cursor):
    league_table = cursor.execute('''
        SELECT *
        FROM Calculations
        ORDER BY points DESC, correct_scores DESC
    ''').fetchall()

    field_names = [x[0] for x in cursor.execute('''
        SELECT *
        FROM Calculations
    ''').description]

    pretty_table = PrettyTable()
    pretty_table.field_names = field_names
    for x in league_table:
        pretty_table.add_row(list(x))

    print(pretty_table)


async def main():
    # flag to check if database already exists
    exists = path.exists("database.db")

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    if not exists:
        # create tables and specify the columns and their datatypes
        initialise_database(cursor)

    async with aiohttp.ClientSession() as session:
        active_round_info = await fetch(session, "https://super6.skysports.com/api/v2/round/active")
        active_round = active_round_info["id"]

        # check for new ID values in IDs.csv and if any are found, add the ID and corresponding name to the Users table
        await update_users(session, cursor)

        # update the Rounds and Results tables
        # in the case of the Rounds table, this is up to and including active_round
        # in the case of the Results table, this is up to but excluding active_round
        await update_multiple_rounds_info_and_results(session, cursor, active_round)

        # update the Predictions table
        await update_multiple_users_multiple_rounds_predictions(session, cursor, active_round)

    # update the calculations table
    await update_multiple_user_calculations(cursor)

    print_final_table(cursor)

    # commit changes and close the connection
    connection.commit()
    connection.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
