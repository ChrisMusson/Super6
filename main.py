import aiohttp
import asyncio
import json
from utils import fetch, login
from setup import username, pin, league_id, spreadsheet_name


async def main():

    with open("predictions.csv", "r") as f:
        rounds_preds = (sum(1 for line in f) - 1) / 6
    if rounds_preds != int(rounds_preds):
        print("There was an unexpected number of rows in your predictions.csv file")
        return -1

    with open("results.csv", "r") as f:
        rounds_results = (sum(1 for line in f) - 1) / 6
    if rounds_results != int(rounds_results):
        print("There was an unexpected number of rows in your results.csv file")
        return -1

    if rounds_preds != rounds_results:
        print("There are a different number of rows in your predictions.csv and results.csv files")
        return -1

    rounds_completed = int(rounds_preds)

    with open("IDs.json", "r") as f:
        IDs = json.load(f)
    num_players = len(IDs)

    async with aiohttp.ClientSession() as session:
        await login(session, username, pin)
        page = await fetch(session, "https://super6.skysports.com/play")


        # gather all rounds up until this current round with in_progress=False (it is by default), then also this current round with it being true
        # tasks_preds = [asyncio.ensure_future(get_predictions(session, round, ID)) for round in rounds_needed[:-1] for ID in IDs.values()] + [
        #     asyncio.ensure_future(get_predictions(session, current_round, ID, in_progress)) for ID in IDs.values()]
        # tasks_results = [asyncio.ensure_future(get_results(session, round)) for round in rounds_needed[:-1]] + [
        #     asyncio.ensure_future(get_results(session, current_round, in_progress))]

        # returns responses in same order as input
        # responses_preds = await asyncio.gather(*tasks_preds)
        # responses_results = await asyncio.gather(*tasks_results)


if __name__ == "__main__":
    asyncio.run(main())
