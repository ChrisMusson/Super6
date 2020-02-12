import aiohttp
import asyncio
import json
import pandas as pd
import pygsheets
from bs4 import BeautifulSoup
from utils import fetch, login, get_predictions, get_results
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
        soup = BeautifulSoup(page, "lxml")

        try:
            next_round = int(
                soup.find("form", class_="predictions-body--old")["data-round"])
        except TypeError:
            print(
                "There is a round in progress. Wait until the next round's fixtures are released")
            return 0

        if next_round - rounds_completed == 1:
            print("Your data is already up to date")
            return 0
        else:
            rounds_needed = list(
                range(rounds_completed + 1, next_round))
            if len(rounds_needed) == 1:
                print(f"Getting data for round {rounds_needed[0]}")
            else:
                print(
                    f"Getting data for rounds {rounds_needed[0]} - {rounds_needed[-1]}")

        tasks_preds = [asyncio.ensure_future(get_predictions(
            session, round, ID)) for round in rounds_needed for ID in IDs.values()]
        tasks_results = [asyncio.ensure_future(
            get_results(session, round)) for round in rounds_needed]

        # returns responses in same order as input
        responses_preds = await asyncio.gather(*tasks_preds)
        responses_results = await asyncio.gather(*tasks_results)

    # restructure predictions into a dataframe with suitable layout
    preds_df = pd.DataFrame()
    for i in range(len(rounds_needed)):
        round_df = pd.DataFrame()
        for preds_lst in responses_preds[num_players * i:num_players * (i + 1)]:
            reshaped = pd.DataFrame(
                data=pd.Series(preds_lst).values.reshape(6, 2))
            round_df = pd.concat([round_df, reshaped],
                                 axis=1, ignore_index=True)
        preds_df = pd.concat([preds_df, round_df],
                             axis=0, ignore_index=True)

    with open("predictions.csv", "a", newline="") as f:
        preds_df.to_csv(f, header=False, index=False)

    results_df = pd.DataFrame()
    for results_lst in responses_results:
        reshaped = pd.DataFrame(data=pd.Series(
            results_lst).values.reshape(6, 2))
        results_df = pd.concat(
            [results_df, reshaped], axis=0, ignore_index=True)

    with open("results.csv", "a", newline="") as f:
        results_df.to_csv(f, header=False, index=False)

    print(f"Writing data to spreadsheet {spreadsheet_name}")

    session = pygsheets.authorize(service_file='creds.json')
    spreadsheet = session.open(spreadsheet_name)

    worksheet = spreadsheet.worksheet('title', 'Predictions')
    data = pd.read_csv("predictions.csv")
    worksheet.set_dataframe(data, 'A1')

    worksheet = spreadsheet.worksheet('title', 'Results')
    data = pd.read_csv("results.csv")
    worksheet.set_dataframe(data, 'A1')


if __name__ == "__main__":
    asyncio.run(main())
