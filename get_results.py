from bs4 import BeautifulSoup


def get_results(s, round):
    results = []
    page = s.get(
        "https://super6.skysports.com/results/round/{}/user/16634526".format(round))
    soup = BeautifulSoup(page.content, "lxml")
    matches = soup.find_all("div", class_="prediction-card--old")

    for match in matches:
        results.append(match.find(
            "div", class_="js-score--live__team1").text.strip())
        results.append(match.find(
            "div", class_="js-score--live__team2").text.strip())

    return results
