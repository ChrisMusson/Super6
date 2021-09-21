import aiohttp
import asyncio
import itertools
import json

from classes.prediction import Prediction
from classes.result import Result
from classes.user import User
from constants import API_URLS
from os import path
from prettytable import from_db_cursor
from SQL import *
from typing import List
from utils import *


class Super6:
    def __init__(self, session: aiohttp.client.ClientSession) -> None:
        self.session = session
        exists = path.exists("database.db")
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            if not exists:
                initialise_database(cursor)

        ignored = read_from_csv("ignored_challenge_ids")
        delete_from_results(cursor, challenge_ids=ignored)

    async def get_results(self, round_number: int) -> List[Result]:
        '''Returns a list of Result objects from the specified round number'''

        data = await fetch(
            self.session,
            API_URLS["round"].format(round_number)
        )

        return [
            Result(
                x["id"],
                round_number,
                x["match"]["homeTeam"]["score"],
                x["match"]["awayTeam"]["score"],
                is_in_past(x["match"]["kickOffDateTime"]),
                x["match"]["status"] == "Match Complete",
                x["void"]
            ) for x in data["scoreChallenges"]
        ]

    async def get_predictions(self, round_number: int, user_id: int) -> List[Prediction]:
        '''Returns a list of Prediction objects from the specified round number and user id'''

        data = await fetch(
            self.session,
            API_URLS["prediction"].format(round_number, user_id)
        )

        if data is None or not data["hasPredicted"]:
            return []

        return [
            Prediction(
                user_id,
                round_number,
                x["challengeId"],
                x["scoreHome"],
                x["scoreAway"]
            ) for x in data["predictions"]["scores"]
        ]

    async def get_user(self, user_id: int) -> User:
        '''Returns a User object from the specified user id'''

        data = await fetch(
            self.session,
            API_URLS["user"].format(user_id)
        )

        return User(
            user_id,
            data["firstName"].strip().title(),
            data["lastName"].strip().title()
        )

    async def get_active_round(self) -> int:
        '''Returns the currently active round'''

        data = await fetch(
            self.session,
            API_URLS["active"]
        )

        return data["id"]

    async def update_users(
        self,
        cursor: sqlite3.Cursor,
        to_add: List[int],
        to_delete: List[int]
    ) -> None:
        '''Updates the Users table in the database'''

        tasks = [self.get_user(user_id) for user_id in to_add]
        users = await asyncio.gather(*tasks)

        delete_from_users(cursor, to_delete)
        insert_into_users(cursor, users)

    async def update_results(
        self,
        cursor: sqlite3.Cursor,
        last_update: dict,
        active_round: int
    ) -> None:
        '''Updates the Results table in the database'''

        start = last_update["round"]
        new_db = start == 0
        finished = last_update["finished"]

        if not finished:
            delete_from_results(cursor, [start])

        tasks = [self.get_results(round_number) for round_number in
                 range(start + new_db + finished, active_round + 1)]
        results = await asyncio.gather(*tasks)
        results = list(itertools.chain(*results))

        insert_into_results(cursor, results)

    async def update_predictions(
        self,
        cursor: sqlite3.Cursor,
        last_update: dict,
        active_round: int,
        to_add: List[int],
        to_delete: List[int],
        IDs_file: List[int]
    ) -> None:
        '''Updates the Predictions table in the database'''

        delete_from_predictions(cursor, to_delete)

        tasks1 = [self.get_predictions(rnd, user_id) for user_id in to_add
                  for rnd in range(1, last_update["round"] + 1)]

        tasks2 = [self.get_predictions(rnd, user_id) for user_id in IDs_file
                  for rnd in range(last_update["round"] + 1, active_round + 1)]

        tasks = tasks1 + tasks2
        predictions = await asyncio.gather(*tasks)
        predictions = list(itertools.chain(*predictions))

        insert_into_predictions(cursor, predictions)

    def update_calculations(self, cursor: sqlite3.Cursor, IDs_file: List[int]) -> None:
        '''Updates the Calculations table in the database'''

        delete_from_calculations(cursor)
        for user_id in IDs_file:
            insert_into_calculations(cursor, user_id)
    
    def print_calculations(self, limit: int = 100) -> None:
        '''Prints out top `limit` users in the Calculations table to the command line'''
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            get_calculations(cursor, limit)
            league_table = from_db_cursor(cursor)
            league_table.float_format = ".2"

        print(league_table)

    async def update_database(self) -> None:
        '''Updates the database with all the latest data'''

        active_round = await self.get_active_round()
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()

            IDs_db = read_ids_from_db(cursor)
            IDs_file = read_from_csv("IDs")

            to_add = [x for x in IDs_file if x not in IDs_db]
            to_delete = [x for x in IDs_db if x not in IDs_file]

            last_update = get_last_update(cursor)

            await self.update_users(cursor, to_add, to_delete)
            await self.update_results(cursor, last_update, active_round)
            await self.update_predictions(cursor, last_update, active_round, to_add, to_delete, IDs_file)
            self.update_calculations(cursor, IDs_file)
