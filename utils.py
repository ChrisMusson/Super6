import aiohttp
import asyncio
import csv

from classes.prediction import Prediction
from datetime import datetime
from typing import List


async def fetch(
    session: aiohttp.client.ClientSession,
    url: str,
    retries: int = 10,
    cooldown: int = 1
) -> dict:
    '''Returns the JSON data from the specified API endpoint'''

    retries_count = 0
    while True:
        async with session.get(url) as response:
            return await response.json()
        retries_count += 1
        if retries_count > retries:
            raise Exception(f"Could not fetch {url} after {retries} retries")

        if cooldown:
            await asyncio.sleep(cooldown)


def is_in_past(dt: str) -> bool:
    '''Returns whether or not the given datetime is in the past'''

    return datetime.strptime(dt, r"%Y-%m-%dT%H:%M:%S.000Z") < datetime.now()


def read_from_csv(file: str) -> List[int]:
    '''Returns a list of the numbers found in {file}.csv'''

    with open(f"{file}.csv", "r") as f:
        reader = csv.reader(f)
        return [int(ID.strip()) for ID in next(reader)]
