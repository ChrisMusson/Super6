import pandas as pd


def get_predictions(driver, round, IDs):
    predictions = []
    for ID in IDs.values():
        driver.get(
            "https://super6.skysports.com/results/round/{}/user/{}".format(round, ID))

        matches = driver.find_elements_by_class_name('prediction-card--old')

        for match in matches:

            if match.find_element_by_class_name('card-header').text == "CORRECT SCORE":
                predictions.append(match.find_element_by_class_name(
                    'js-score--live__team1').text)
                predictions.append(match.find_element_by_class_name(
                    'js-score--live__team2').text)

            else:
                predictions.append(match.find_element_by_class_name(
                    'js-score--live__pred1').text)
                predictions.append(match.find_element_by_class_name(
                    'js-score--live__pred2').text)

    # convert predictions from string to int where possible
    predictions = [x if x == '-' or x == '' else int(x) for x in predictions]

    # split predictions into chunks of 12 (each person's set of predictions for that round)
    predictions_split = [predictions[i:i + 12]
                         for i in range(0, len(predictions), 12)]

    dataframe = pd.DataFrame()
    for lst in predictions_split:
        # reshape each chunk of 12 to 6 rows of 2 columns (6 matches of Home and Away predictions)
        reshaped = pd.DataFrame(data=pd.Series(lst).values.reshape(6, 2))
        # concatenate each of these so the df is in the format specified in the table below
        dataframe = pd.concat([dataframe, reshaped], axis=1, ignore_index=True)

    return dataframe

    '''
    changes the order of predictions in the list from
    P1M1H, P1M1A, P1M2H, P1M2A, ... P1M6A, P2M1H, ... to
    P1M1H, P1M1A, P2M1H, P2M1A, ... PNM1A, P1M1H, P1M1A...

    as the final table of predictions will be formatted like so:
    ___________________________________________________ ...
    |         |   P1  |   P2  |   P3  |   P4  |   P5  | ...
    |         |_______|_______|_______|_______|_______| ...
    |         | H | A | H | A | H | A | H | A | H | A | ...
    |____ ____|___|___|___|___|___|___|___|___|___|___| ...
    |    | M1 |   |   |   |   |   |   |   |   |   |   | ...
    |    |____|___|___|___|___|___|___|___|___|___|___| ...
    |    | M2 |   |   |   |   |   |   |   |   |   |   | ...
    |    |____|___|___|___|___|___|___|___|___|___|___| ...
    | R1 | M3 |   |   |   |   |   |   |   |   |   |   | ...
    |    |____|___|___|___|___|___|___|___|___|___|___| ...
       .   .    .   .   .   .   .   .   .   .   .   .
       .   .    .   .   .   .   .   .   .   .   .   .
       .   .    .   .   .   .   .   .   .   .   .   .
    where P=player, R=round, and M=match
    '''
