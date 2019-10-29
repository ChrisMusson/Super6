import pandas as pd


def get_results(driver, round):
    results = []

    matches = driver.find_elements_by_class_name('prediction-card--old')

    for match in matches:

        results.append(match.find_element_by_class_name(
            'js-score--live__team1').text)
        results.append(match.find_element_by_class_name(
            'js-score--live__team2').text)

    # converting results from string to int
    results = [int(x) for x in results]

    # changing the order of the results to a more suitable order and converting the array to a dataframe object
    reshaped = pd.DataFrame(data=pd.Series(results).values.reshape(6, 2))

    return reshaped
