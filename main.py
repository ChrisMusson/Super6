from setup import username, pin, league_id, spreadsheet_name
import requests
from login import login
import json
from get_predictions import get_predictions
from get_results import get_results
import pandas as pd
from bs4 import BeautifulSoup
import pygsheets


def main():
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

    rounds = int(rounds_preds)

    with open("IDs.json", "r") as f:
        IDs = json.load(f)

    with requests.Session() as s:
        login(s, username, pin)
        page = s.get("https://super6.skysports.com/play")
        soup = BeautifulSoup(page.content, "lxml")
        try:
            next_round = int(
                soup.find("form", class_="predictions-body--old")["data-round"])
        except TypeError:
            print(
                "There is a round in progress. Wait until the next round's fixtures are released")
            return 0

        difference = next_round - rounds

        if difference == 1:
            print("Your data is already up to date")
            return 0

        else:
            for i in range(rounds + 1, next_round):
                print("getting data for round {}".format(i))

                all_predictions_for_round = []
                for ID in IDs.values():
                    all_predictions_for_round.append(get_predictions(s, i, ID))

                predictions = pd.DataFrame()
                for lst in all_predictions_for_round:
                    # reshape each chunk of 12 predictions to 6 rows of 2 columns (6 matches of Home and Away predictions)
                    reshaped = pd.DataFrame(
                        data=pd.Series(lst).values.reshape(6, 2))
                    # put these together horizontally to form 6 rows of P1 Home, P1 Away, P2 Home, P2 Away etc
                    predictions = pd.concat(
                        [predictions, reshaped], axis=1, ignore_index=True)

                with open("predictions.csv", "a", newline="") as f:
                    predictions.to_csv(f, header=False, index=False)

                results = get_results(s, i)
                reshaped = pd.DataFrame(
                    data=pd.Series(results).values.reshape(6, 2))

                with open("results.csv", "a", newline="") as f:
                    reshaped.to_csv(f, header=False, index=False)

    print("Writing the predictions and scores to the spreadsheet {}".format(
        spreadsheet_name))

    session = pygsheets.authorize(service_file='creds.json')
    spreadsheet = session.open(spreadsheet_name)

    worksheet = spreadsheet.worksheet('title', 'Predictions')
    data = pd.read_csv("predictions.csv")
    worksheet.set_dataframe(data, 'A1')

    worksheet = spreadsheet.worksheet('title', 'Results')
    data = pd.read_csv("results.csv")
    worksheet.set_dataframe(data, 'A1')


if __name__ == "__main__":
    main()
