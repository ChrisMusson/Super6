from login import login
import requests
from bs4 import BeautifulSoup
import json
import csv
import pygsheets
import pandas as pd

username = ""
pin = ""
league_id = ""
spreadsheet_name = ""


def main():
    with requests.Session() as s:
        login(s, username, pin)
        league_page = s.get(
            "https://super6.skysports.com/league/{}/season".format(league_id))

    soup = BeautifulSoup(league_page.content, "lxml")
    rows = soup.find_all("table")[1].find_all("tr")

    names = [str(row.div)[5:-6].title() for row in rows[1:]]
    IDs = [row["data-dest-id"] for row in rows[1:]]

    # create a Name:ID dictionary sorted in alphabetical order
    IDs_dict = dict(sorted(dict(zip(names, IDs)).items()))

    # save this dictionary to a new file
    with open("IDs.json", "w") as f:
        f.write(json.dumps(IDs_dict))

    names.sort()
    initials = [''.join([x[0].upper() for x in fullname.split(' ')])
                for fullname in names]

    # if any initials are duplicates, append a 1, 2, 3 etc until they are all unique
    if len(set(initials)) != len(initials):
        to_update = [i for i, initial in enumerate(
            initials) if initials.count(initial) > 1]
        for j, k in enumerate(to_update, 1):
            initials[k] += " {}".format(str(j))

    # headers for the 'Predictions' data
    predictions_headers = []
    for initial in initials:
        predictions_headers.append(initial + " H")
        predictions_headers.append(initial + " A")

    results_headers = ["Home", "Away"]

    with open("predictions.csv", "w", newline="") as f:
        wr = csv.writer(f, delimiter=",")
        wr.writerow(predictions_headers)

    with open("results.csv", "w", newline="") as f:
        wr = csv.writer(f, delimiter=",")
        wr.writerow(results_headers)

    num_players = len(rows) - 1

    session = pygsheets.authorize(service_file='creds.json')
    ss = session.open(spreadsheet_name)

    ss.add_worksheet(title="Predictions", rows=600, cols=num_players * 2)
    ss.add_worksheet(title="Results", rows=600, cols=2)

    ss.add_worksheet(title="Points", rows=100, cols=num_players)
    wks = ss.worksheet_by_title("Points")
    formula = "= ARRAYFORMULA(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = \"-\", \"-\", IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = \"\", \"\", IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = Results!A2:A, 1, 0) * IF(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2) = Results!B2:B, 1, 0) = 1, 5, IF(IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) > OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A > Results!B2:B, 1, 0) = 1, 1, 0) + IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) < OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A < Results!B2:B, 1, 0) = 1, 1, 0) + IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A = Results!B2:B, 1, 0) = 1, 1, 0) > 0, 2, 0)))))"
    wks.update_row(1, initials)
    wks.update_row(2, [formula] * num_players)

    ss.add_worksheet(title="PointsByRound", rows=100, cols=num_players)
    wks = ss.worksheet_by_title("PointsByRound")
    formula = "= IF(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1) = \"\", \"\", IF(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1) = \"-\", \"-\", SUM(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1, 6, 1))))"
    wks.update_row(1, initials)
    df = pd.DataFrame([[formula] * num_players] * 99)
    wks.set_dataframe(df, "A2", copy_head=False)

    ss.add_worksheet(title="TableCalculation", rows=12, cols=num_players + 1)
    wks = ss.worksheet_by_title("TableCalculation")
    wks.update_row(1, names, 1)
    wks.update_col(1, ["Rounds", "Played", "Results", "Scores", "Points",
                                 "Pts / Round", "Std. Dev.", "Off By 1", "Off By 2", "Off By 3", "Off By 4+"], 1)

    # initialise dataframe that will hold all the formulas to go into this worksheet
    df = pd.DataFrame()

    formula_rounds = "= (COUNTIF(Predictions!A2:A, \"-\") + COUNTIF(Predictions!A2:A, \">=0\")) / 6"
    df = df.append([formula_rounds])

    formula_played = "= COUNTIF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4), \">=0\") / 6"
    df = df.append([formula_played])

    formula_results = "= COUNTIF(OFFSET(Points!A2:A, 0, COLUMN() - 2), 2)"
    df = df.append([formula_results])

    formula_scores = "= COUNTIF(OFFSET(Points!A2:A, 0, COLUMN() - 2), 5)"
    df = df.append([formula_scores])

    formula_points = "= 2 * OFFSET(B4, 0, COLUMN() - 2) + 5 * OFFSET(B5, 0, COLUMN() - 2)"
    df = df.append([formula_points])

    formula_points_per_round = "= IFERROR(OFFSET(B6, 0, COLUMN() - 2) / OFFSET(B3, 0, COLUMN() - 2), 0)"
    df = df.append([formula_points_per_round])

    formula_SD = "= IFERROR(STDEV(OFFSET(PointsByRound!A2, 0, COLUMN() - 2, 100, 1)), 0)"
    df = df.append([formula_SD])

    formula_off_by_one = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 1, FALSE))))"
    df = df.append([formula_off_by_one])

    formula_off_by_two = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 2, FALSE))))"
    df = df.append([formula_off_by_two])

    formula_off_by_three = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 3, FALSE))))"
    df = df.append([formula_off_by_three])

    formula_off_by_four_plus = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) >= 4, FALSE))))"
    df = df.append([formula_off_by_four_plus])

    # give this dataframe the same number of columns as there are number of players
    for i in range(1, num_players):
        df[i] = df[0]

    wks.set_dataframe(df, "B2", copy_head=False)

    ss.add_worksheet(title="Table", rows=num_players + 1, cols=12)
    wks = ss.worksheet_by_title("Table")
    wks.update_value(
        "A1", "= SORT(TRANSPOSE(OFFSET(TableCalculation!A1, 0, 0, 12, {})), 6, FALSE, 7, FALSE, 5, FALSE, 1, TRUE)".format(num_players + 1))

    wks = ss.worksheet('index', 0)
    ss.del_worksheet(wks)


if __name__ == "__main__":
    main()
