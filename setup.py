league_ID = ""
username = ""
pin = ""
spreadsheet_name = ""


def main():
    from selenium import webdriver
    from login import login
    import json
    import csv
    import pygsheets
    import pandas as pd

    driver = webdriver.Chrome()
    login(driver=driver, username=username, pin=pin)

    driver.get("https://super6.skysports.com/league/{}/season".format(league_ID))

    rows = driver.find_elements_by_class_name("table-row")

    IDs = [row.get_attribute("data-dest-id") for row in rows[1:]]
    names = [row.find_element_by_tag_name(
        "div").text.upper() for row in rows[1:]]

    ID_dict = dict(zip(names, IDs))
    ID_dict = dict(sorted(ID_dict.items()))

    sorted_names = sorted(names)

    headers, list_initials = [], []
    for name in sorted_names:
        initials = ''.join([x[0].upper() for x in name.split(' ')])
        list_initials.append(initials)
        headers.append(initials + "_H")
        headers.append(initials + "_A")

    first_names = [name.split()[0].capitalize() for name in sorted_names]

    # check which first names, if any, are duplicates
    indexes_to_change = [i for i, name in enumerate(
        first_names) if first_names.count(name) > 1]

    # add second initial to any that are duplicates
    for i in indexes_to_change:
        first_names[i] += " {}".format(sorted_names[i].split()[1][0].upper())

    with open("IDs.json", "w") as f:
        f.write(json.dumps(ID_dict))

    with open("predictions.csv", "w", newline="") as f:
        wr = csv.writer(f, delimiter=",")
        wr.writerow(headers)

    with open("results.csv", "w", newline="") as f:
        wr = csv.writer(f, delimiter=",")
        wr.writerow(["Home", "Away"])

    num_players = len(rows) - 1

    session = pygsheets.authorize(service_file='creds.json')
    ss = session.open(spreadsheet_name)

    ss.add_worksheet(title="Predictions", rows=600, cols=num_players * 2)
    wks = ss.worksheet_by_title("Predictions")

    ss.add_worksheet(title="Results", rows=600, cols=2)
    wks = ss.worksheet_by_title("Results")

    ss.add_worksheet(title="Points", rows=100, cols=num_players)
    wks = ss.worksheet_by_title("Points")
    formula = "= ARRAYFORMULA(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = \"-\", \"-\", IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = \"\", \"\", IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = Results!A2:A, 1, 0) * IF(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2) = Results!B2:B, 1, 0) = 1, 5, IF(IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) > OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A > Results!B2:B, 1, 0) = 1, 1, 0) + IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) < OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A < Results!B2:B, 1, 0) = 1, 1, 0) + IF(IF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 2) = OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 2), 1, 0) * IF(Results!A2:A = Results!B2:B, 1, 0) = 1, 1, 0) > 0, 2, 0)))))"
    wks.update_row(1, list_initials)
    wks.update_row(2, [formula] * num_players)

    ss.add_worksheet(title="PointsByRound", rows=100, cols=num_players)
    wks = ss.worksheet_by_title("PointsByRound")
    formula = "= IF(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1) = \"\", \"\", IF(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1) = \"-\", \"-\", SUM(OFFSET(Points!A2, ROW() * 6 - 12, COLUMN() - 1, 6, 1))))"
    wks.update_row(1, list_initials)

    df = pd.DataFrame([[formula] * num_players] * 99)
    wks.set_dataframe(df, "A2", copy_head=False)

    ss.add_worksheet(title="TableCalculation", rows=12, cols=num_players + 1)
    wks = ss.worksheet_by_title("TableCalculation")

    wks.update_row(1, first_names, 1)
    wks.update_col(1, ["Rounds", "Played", "Results", "Scores", "Points",
                                 "Pts / Round", "Std. Dev.", "Off By 1", "Off By 2", "Off By 3", "Off By 4+"], 1)

    formula_rounds = "= (COUNTIF(Predictions!A2:A, \"-\") + COUNTIF(Predictions!A2:A, \">=0\")) / 6"
    wks.update_row(2, [formula_rounds] * num_players, 1)

    formula_played = "= COUNTIF(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4), \">=0\") / 6"
    wks.update_row(3, [formula_played] * num_players, 1)

    formula_results = "= COUNTIF(OFFSET(Points!A2:A, 0, COLUMN() - 2), 2)"
    wks.update_row(4, [formula_results] * num_players, 1)

    formula_scores = "= COUNTIF(OFFSET(Points!A2:A, 0, COLUMN() - 2), 5)"
    wks.update_row(5, [formula_scores] * num_players, 1)

    formula_points = "= 2 * OFFSET(B4, 0, COLUMN() - 2) + 5 * OFFSET(B5, 0, COLUMN() - 2)"
    wks.update_row(6, [formula_points] * num_players, 1)

    formula_points_per_round = "= IFERROR(OFFSET(B6, 0, COLUMN() - 2) / OFFSET(B3, 0, COLUMN() - 2), 0)"
    wks.update_row(7, [formula_points_per_round] * num_players, 1)

    formula_SD = "= IFERROR(STDEV(OFFSET(PointsByRound!A2, 0, COLUMN() - 2, 100, 1)), 0)"
    wks.update_row(8, [formula_SD] * num_players, 1)

    formula_off_by_one = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 1, FALSE))))"
    wks.update_row(9, [formula_off_by_one] * num_players, 1)

    formula_off_by_two = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 2, FALSE))))"
    wks.update_row(10, [formula_off_by_two] * num_players, 1)

    formula_off_by_three = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) = 3, FALSE))))"
    wks.update_row(11, [formula_off_by_three] * num_players, 1)

    formula_off_by_four_plus = "= SUM(ARRAYFORMULA(N(IFERROR(ABS(OFFSET(Predictions!A2:A, 0, 2 * COLUMN() - 4) - Results!A2:A) + ABS(OFFSET(Predictions!B2:B, 0, 2 * COLUMN() - 4) - Results!B2:B) >= 4, FALSE))))"
    wks.update_row(12, [formula_off_by_four_plus] * num_players, 1)

    ss.add_worksheet(title="Table", rows=num_players + 1, cols=12)
    wks = ss.worksheet_by_title("Table")
    wks.update_value(
        "A1", "= SORT(TRANSPOSE(OFFSET(TableCalculation!A1, 0, 0, 12, {})), 6, FALSE, 7, FALSE, 5, FALSE, 1, TRUE)".format(num_players + 1))

    wks = ss.worksheet('index', 0)
    ss.del_worksheet(wks)


if __name__ == "__main__":
    main()
