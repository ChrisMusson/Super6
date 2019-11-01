import requests


def login(s, username, pin):
    login_url = "https://www.skybet.com/secure/identity/m/login/super6"
    params = {"username": username, "pin": pin}

    # Initially copied all request headers from making a normal request in a browser, but it turns out the only one needed is the X-Requested-With header.
    # They have been left in but commented out in case this changes in the future
    headers = {
        # "Host": "www.skybet.com",
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36",
        # "Accept": "application/json",
        # "Accept-Language": "en-GB,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,en-US;q=0.6",
        # "Accept-Encoding": "gzip, deflate, br",
        # "Referer": "https://www.skybet.com/secure/identity/m/login/super6?urlconsumer=https://super6.skysports.com&dl=1",
        # "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        # "Origin": "https://www.skybet.com",
        # "Content-Length": "65",
        # "Connection": "keep-alive",
        # "DNT": "1",
        # "Sec-Fetch-Mode": "cors",
        # "Sec-Fetch-Site": "same-origin"
    }

    token_json = s.post(login_url, json=params, headers=headers)
    user_token = token_json.json()["user_data"]["ssoToken"]
    s.post("https://super6.skysports.com/auth/login",
           data={"token": user_token})
