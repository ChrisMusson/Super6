import sqlite3
from os import path
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

    for user_id in users_to_add:
        user_data = await fetch(session, f"https://super6.skysports.com/api/v2/score/leaderboard/user/{user_id}?period=season")
        first_name, last_name = user_data["firstName"], user_data["lastName"]

        cursor.execute('''INSERT INTO Users VALUES(?, ?, ?)''',
                       (user_id, first_name.capitalize(), last_name.capitalize()))

async def update_single_round_info_and_results(session, cursor, round_number, active_round):
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

async def main():
    # flag to check if database already exists
    exists = path.exists("database.db")

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    if not exists:
        # creates tables and specifies the columns and the datatypes of said columns
        initialise_database(cursor)

    async with aiohttp.ClientSession() as session:
        active_round_info = await fetch(session, "https://super6.skysports.com/api/v2/round/active")
        active_round = active_round_info["id"]

        # checks for new ID values in IDs.csv and if any are found, adds the ID and corresponding name to the Users table
        await update_users(session, cursor)

        # updates the Rounds and Results tables
        # in the case of the Rounds table, this is up to and including active_round
        # in the case of the Results table, this is up to but excluding active_round
        await update_multiple_rounds_info_and_results(session, cursor, active_round)

        # updates the Predictions table
        await update_multiple_users_multiple_rounds_predictions(session, cursor, active_round)

    # commit changes and close the connection
    connection.commit()
    connection.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
