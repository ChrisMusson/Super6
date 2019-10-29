from selenium import webdriver
from login import login
from setup import username, pin, spreadsheet_name
from get_predictions import get_predictions
from get_results import get_results
import pygsheets
import pandas as pd
import json


def main(start, end=False):

    if not end:
        end = start

    driver = webdriver.Chrome()
    login(driver=driver, username=username, pin=pin)

    with open("IDs.json", "r") as f:
        IDs = json.load(f)

    for i in range(start, end + 1):
        print("Getting predictions and results for round {}".format(i))

        predictions = get_predictions(driver=driver, round=i, IDs=IDs)
        results = get_results(driver=driver, round=i)

        with open("predictions.csv", "a", newline="") as f:
            predictions.to_csv(f, header=False, index=False)

        with open("results.csv", "a", newline="") as f:
            results.to_csv(f, header=False, index=False)

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
    main(1, 17)
