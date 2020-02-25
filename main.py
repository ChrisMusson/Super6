import aiohttp
import asyncio
import json
import pandas as pd
import pygsheets
from bs4 import BeautifulSoup
from utils import fetch, login, get_predictions, get_results, print_rounds_needed
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
            # this element is only available when a round is not in progress
            next_round = int(
                soup.find("form", class_="predictions-body--old")["data-round"])
            in_progress = False

        except TypeError:
            # the next round's fixtures are not available yet
            # this is important because the relevant URLs are different when a round is in progress
            in_progress = True

            current_round = int(
                soup.find("h2", class_="panel-header").text.strip()[6:])
            matches = soup.find_all("div", class_="prediction-card--old")
            for match in matches:
                try:
                    # if there is a match in progress, stop the program
                    if match.find("span", class_="live-flag").text == "LIVE":
                        print(
                            "There is a round in progress. Wait until all matches have been completed")
                        return -1
                except AttributeError:
                    # the match has no live-flag so the game has finished, and shouldn't cause us to stop the program
                    continue

        '''
        if the program gets to this point, it means that either the round is not in progress,
        or that the round is in progress but all matches have finished
        '''

        if not in_progress:
            if next_round - rounds_completed == 1:
                print("Your data is already up to date")
                return -1
            else:
                rounds_needed = list(range(rounds_completed + 1, next_round))
                print_rounds_needed(rounds_needed)
                # don't have to worry about the in-play argument or URLs being different for different rounds when fetching data
                tasks_preds = [asyncio.ensure_future(get_predictions(
                    session, round, ID)) for round in rounds_needed for ID in IDs.values()]
                tasks_results = [asyncio.ensure_future(
                    get_results(session, round)) for round in rounds_needed]

        else:  # in_progress=True
            if current_round - rounds_completed == 0:
                print("Your data is already up to date")
                return -1
            else:
                rounds_needed = list(
                    range(rounds_completed + 1, current_round + 1))
                print_rounds_needed(rounds_needed)
                # gather all rounds up until this current round with in_progress=False (it is by default), then also this current round with it being true
                tasks_preds = [asyncio.ensure_future(get_predictions(session, round, ID)) for round in rounds_needed[:-1] for ID in IDs.values()] + [
                    asyncio.ensure_future(get_predictions(session, current_round, ID, in_progress)) for ID in IDs.values()]
                tasks_results = [asyncio.ensure_future(get_results(session, round)) for round in rounds_needed[:-1]] + [
                    asyncio.ensure_future(get_results(session, current_round, in_progress))]

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
