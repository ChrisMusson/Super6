import csv
import requests
import sys

try:
    import simplejson as json
except:
    import json

def get_user_IDs(username, pin, league_id):
    with requests.Session() as s:
        login_url = "https://www.skybet.com/secure/identity/m/login/super6"
        params = {"username": username, "pin": pin}
        headers = {"X-Requested-With": "XMLHttpRequest"}

        post = s.post(login_url, json=params, headers=headers).json()

        try:
            sso_token = post["user_data"]["ssoToken"]
        except KeyError:
            print("\nYour username or password is incorrect\n")
            sys.exit(1)

        headers = {"authorization": f"sso {sso_token}"}

        all_ids = []
        page = 1
        while True:
            try:
                url = f"https://api.s6.sbgservices.com/v2/score/league/{league_id}?period=season&page={page}"
                user_data = s.get(url, headers=headers).json()
                for user in user_data:
                    all_ids.append(user["userId"])
                page += 1
            except (json.decoder.JSONDecodeError, json.errors.JSONDecodeError):
                if page == 1:
                    print("\nThere was a problem getting data from the specified league ID\n")
                    sys.exit(1)
                break

        return all_ids


def main():
    assert len(sys.argv) == 4, "The program must be run as 'python get_IDs.py <username> <pin> <league_id>'"
    username, pin, league_id = sys.argv[1:]
    id_list = get_user_IDs(username, pin, league_id)
    with open("IDs.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(id_list)


if __name__ == "__main__":
    main()
