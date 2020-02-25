from bs4 import BeautifulSoup


async def fetch(session, url):
    async with session.get(url) as resp:
        assert resp.status == 200
        return await resp.text()


async def login(session, username, pin):
    login_url = "https://www.skybet.com/secure/identity/m/login/super6"
    params = {"username": username, "pin": pin}
    # Only header that is necessary
    headers = {"X-Requested-With": "XMLHttpRequest"}

    post = await session.post(login_url, json=params, headers=headers)
    token_json = await post.json()
    ssoToken = token_json["user_data"]["ssoToken"]

    await session.post("https://super6.skysports.com/auth/login",
                       data={"token": ssoToken})


async def get_predictions(session, round, ID, in_progress=False):
    if not in_progress:
        page = await fetch(session, f"https://super6.skysports.com/results/round/{round}/user/{ID}")
    else:
        page = await fetch(session, f"https://super6.skysports.com/inplay/user/{ID}")
    soup = BeautifulSoup(page, "lxml")
    predictions = []
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


async def get_results(session, round, in_progress=False):
    if not in_progress:
        page = await fetch(session, f"https://super6.skysports.com/results/round/{round}/user/15977871")
    else:
        page = await fetch(session, f"https://super6.skysports.com/inplay/user/15977871")
    soup = BeautifulSoup(page, "lxml")
    results = []
    matches = soup.find_all("div", class_="prediction-card--old")
    for match in matches:
        results.append(match.find(
            "div", class_="js-score--live__team1").text.strip())
        results.append(match.find(
            "div", class_="js-score--live__team2").text.strip())
    return results


def print_rounds_needed(rounds_needed):
    '''rounds_needed is a list of consecutive numbers'''
    if len(rounds_needed) == 1:
        print(f"Getting data for round {rounds_needed[0]}")
    else:
        print(
            f"Getting data for rounds {rounds_needed[0]} - {rounds_needed[-1]}")
