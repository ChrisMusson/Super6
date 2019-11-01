from bs4 import BeautifulSoup


def get_predictions(s, round, user_id):

    predictions = []
    page = s.get(
        "https://super6.skysports.com/results/round/{}/user/{}".format(round, user_id))
    soup = BeautifulSoup(page.content, "lxml")
    matches = soup.find_all("div", class_="prediction-card--old")

    for match in matches:
        if match.find("p", class_="card-header").text == "CORRECT SCORE":
            predictions.append(match.find(
                "div", class_="js-score--live__team1").text.strip())
            predictions.append(match.find(
                "div", class_="js-score--live__team2").text.strip())

        else:
            predictions.append(match.find(
                "div", class_="js-score--live__pred1").text.strip())
            predictions.append(match.find(
                "div", class_="js-score--live__pred2").text.strip())

    return predictions
