import sqlite3
from os import path
from prettytable import from_db_cursor
import csv
import json
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
            round_number int,
            match_id int
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


async def update_users(session, cursor, last_updated_round, exists, in_play):
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
            
            # update predictions so that everyone is at the same point
            # only want to do this if the database already exists with users in it - otherwise the usual logic will take care of it
            if exists:
                await add_multiple_users_multiple_rounds_predictions(session, cursor, [user_id], 1, last_updated_round - 1 + in_play)

        except AssertionError:
            print(
                f"The webpage 'https://super6.skysports.com/api/v2/score/leaderboard/user/{user_id}?period=season' could not be reached. This may be because you are not connected to the internet, or because user_id {user_id} is not a valid ID.")

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


async def add_single_round_info_and_results(session, cursor, round_number):
    # Completely ignore round 50 as that was voided with no points awarded due to COVID 19
    if round_number != 50:
        data = await fetch(session, f"https://super6.skysports.com/api/v2/round/{round_number}")

        for match in data["scoreChallenges"]:
            info = match["match"]

            cursor.execute('''
                INSERT INTO Rounds
                VALUES (?, ?)
            ''', (round_number, info["id"]))

            cursor.execute('''
                INSERT INTO Results
                VALUES (?, ?, ?, ?)
            ''', (info["id"], round_number, info["homeTeam"]["score"], info["awayTeam"]["score"]))


async def delete_from_rounds(cursor, round_number):
    cursor.execute('''
        DELETE FROM Rounds
        WHERE round_number = ?
    ''', (round_number,))


async def delete_from_results(cursor, round_number):
    cursor.execute('''
        DELETE FROM Results
        WHERE round_number = ?
    ''', (round_number,))


async def add_multiple_rounds_info_and_results(session, cursor, start, end):
    tasks = []

    for round_number in range(start, end + 1):
        tasks.append(add_single_round_info_and_results(
            session, cursor, round_number))

    return await asyncio.gather(*tasks)


async def add_single_user_single_round_predictions(session, cursor, user_id, round_number):
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


async def add_multiple_users_multiple_rounds_predictions(session, cursor, user_ids, start, end):
    tasks = []
    for round_number in range(start, end + 1):
        for user_id in user_ids:
            tasks.append(add_single_user_single_round_predictions(
                session, cursor, user_id, round_number))

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


async def add_single_user_calculations(cursor, user_id):

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

    points = correct_scores * 5 + correct_results * 2

    off_by_1 = off_by(cursor, user_id, 1)
    off_by_2 = off_by(cursor, user_id, 2)
    off_by_3 = off_by(cursor, user_id, 3)
    off_by_4_or_more = off_by(cursor, user_id, 4, exactly=False)

    if rounds_played > 0:
        pts_per_round = round(points / rounds_played, 2)
    else:
        pts_per_round = 0

    variance = cursor.execute('''
        SELECT ROUND(AVG(round_score*round_score) - AVG(round_score)*AVG(round_score), 2) variance
        FROM(
            SELECT sum(
                2 * (
                        (
                            (x.home - x.away > 0 AND  Results.home - Results.away > 0)
                        OR (x.home - x.away = 0 AND  Results.home - Results.away = 0)
                        OR (x.home - x.away < 0 AND  Results.home - Results.away < 0)
                        )	
                        AND (x.home != Results.home OR x.away != Results.away)
                )
                + 
                5 * (abs(x.home - Results.home) + abs(x.away - Results.away) = 0)
            ) round_score
                        
            FROM (SELECT * FROM Predictions WHERE user_id = ?) x
            INNER JOIN Results
            ON x.match_id = Results.match_id
            GROUP BY x.round_number)
    ''', (user_id,)).fetchone()[0]

    cursor.execute('''
        INSERT INTO Calculations
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (user_id, user_name, rounds_played, correct_results, correct_scores, points, pts_per_round, variance, off_by_1, off_by_2, off_by_3, off_by_4_or_more))


async def add_multiple_users_calculations(cursor, user_ids):
    tasks = []
    for user_id in user_ids:
        tasks.append(add_single_user_calculations(cursor, user_id))
    return await asyncio.gather(*tasks)


def print_final_table(cursor):
    cursor.execute('''
        SELECT *
        FROM Calculations
        ORDER BY points DESC, scores DESC
    ''')

    league_table = from_db_cursor(cursor)
    league_table.float_format = ".2"

    print(league_table)


async def main():
    # flag to check if database already exists
    exists = path.exists("database.db")

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    if not exists:
        # create tables and specify the columns and their datatypes
        initialise_database(cursor)

    with open('last_update.json') as f:
        last_update = json.load(f)

    async with aiohttp.ClientSession() as session:
        active_round_info = await fetch(session, "https://super6.skysports.com/api/v2/round/active")

        active_round = active_round_info["id"]
        in_play = active_round_info["status"] in ["inplay", "complete"]

        last_updated_round = last_update["round"]
        last_update_status = last_update["in_play"]
        
        # add / delete users from tables based on the IDs in IDs.csv and update newly added users to the same point as everyone else
        await update_users(session, cursor, last_updated_round, exists, in_play)

        last_updated_round = last_update["round"]
        last_update_status = last_update["in_play"]

        if last_update_status:
            # neither of these are necessary but it's only a small performance hit and makes the logic easier
            await delete_from_results(cursor, last_updated_round)
            await delete_from_rounds(cursor, last_updated_round)

        # always want to start at the last updated round as that has just been deleted from both tables
        # want to end at current active round only if the round is currently in play, otherwise the one before
        await add_multiple_rounds_info_and_results(session, cursor, last_updated_round, active_round - 1 + in_play)

        user_ids = [x[0] for x in cursor.execute('''
            SELECT user_id
            FROM Users
        ''').fetchall()]

        # logic to decide if the predictions table needs to be updated. If it does, update it
        if last_updated_round + last_update_status < active_round + in_play:
            await add_multiple_users_multiple_rounds_predictions(session, cursor, user_ids, last_updated_round + last_update_status, active_round - 1 + in_play)

    # recalculate everything in calculations table with new results/predictions
    cursor.execute('''
        DELETE FROM Calculations
    ''')
    await add_multiple_users_calculations(cursor, user_ids)

    print_final_table(cursor)

    # commit changes and close the connection
    connection.commit()
    connection.close()

    with open("last_update.json", "w") as f:
        json.dump(
            {
                "round": active_round,
                "in_play": in_play
            }, f
        )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
