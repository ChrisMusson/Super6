import sys
sys.path.insert(0, "..")
from main import *


def write_html_to_file(cursor):
    # there should be a more elegant way of doing this than manually creating the html file myself
    cursor.execute('''
        SELECT RANK () OVER (ORDER BY points DESC) as pos, name, played, results, scores, points, pts_per_round as `pts per round`, variance, off_by_1 as `off by 1`, off_by_2 as `off by 2`, off_by_3 as `off by 3`, off_by_more as `off by 4+`
        FROM Calculations
        ORDER BY points DESC, scores DESC
    ''')

    col_names = [description[0] for description in cursor.description]
    descriptions = {
        "pos": "Position in the league table",
        "name": "User's name",
        "played": "Rounds entered",
        "results": "Correct results",
        "scores": "Correct scores",
        "points": "Total points",
        "pts per round": "Points per round played",
        "variance": "Variance - a measure of consistency. Low variance = consistent",
        "off by 1": "The number of times a user's prediction was off by exactly 1 goal",
        "off by 2": "The number of times a user's prediction was off by exactly 2 goals",
        "off by 3": "The number of times a user's prediction was off by exactly 3 goals",
        "off by 4+": "The number of times a user's prediction was off by at least 4 goals"
    }
    league_table = from_db_cursor(cursor, start=0, end=50)
    league_table.float_format = ".2"

    with open("helper/base_html.html", "r") as f:
        a = f.read()
        pre_table = a.split("<table")[0]
        post_table = a.split("table>")[-1]
        html = pre_table + league_table.get_html_string(attributes={"id":"table"}) + post_table

        b = html.split("<th>")
        full_html = b[0]
        for i, h in enumerate(b[1:]):
            h = f"<th title=\"{descriptions[col_names[i]]}\" onclick=\"sortTable({i})\">" + h
            full_html += h

    with open("index.html", "w") as f:
        f.write(full_html)


async def main():
    # flag to check if database already exists
    exists = path.exists("database.db")

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    if not exists:
        # create tables and specify the columns and their datatypes
        initialise_database(cursor)
        # set the last_update to the initial conditions so the program runs all the way from gameweek 1
        # this is useful if the database file accidentally ever gets deleted or lost
        last_update = {"round": 1, "in_play": False}
    else:
        with open('last_update.json') as f:
            last_update = json.load(f)

    async with aiohttp.ClientSession() as session:
        active_round_info = await fetch(session, "https://super6.skysports.com/api/v2/round/active")

        active_round = active_round_info["id"]
        in_play = active_round_info["status"] in ["inplay", "complete"]

        last_updated_round = last_update["round"]
        last_update_status = last_update["in_play"]
        
        # add / delete users from tables based on the IDs in IDs.csv and update newly added users to the same point as everyone else
        await update_users(session, cursor, last_updated_round, exists, in_play)

        last_updated_round = last_update["round"]
        last_update_status = last_update["in_play"]

        if last_update_status:
            # neither of these are necessary but it's only a small performance hit and makes the logic easier
            await delete_from_results(cursor, last_updated_round)
            await delete_from_rounds(cursor, last_updated_round)

        # always want to start at the last updated round as that has just been deleted from both tables
        # want to end at current active round only if the round is currently in play, otherwise the one before
        await add_multiple_rounds_info_and_results(session, cursor, last_updated_round, active_round - 1 + in_play)

        user_ids = [x[0] for x in cursor.execute('''
            SELECT user_id
            FROM Users
        ''').fetchall()]

        # logic to decide if the predictions table needs to be updated. If it does, update it
        if last_updated_round + last_update_status < active_round + in_play:
            await add_multiple_users_multiple_rounds_predictions(session, cursor, user_ids, last_updated_round + last_update_status, active_round - 1 + in_play)

    # recalculate everything in calculations table with new results/predictions
    cursor.execute('''
        DELETE FROM Calculations
    ''')
    await add_multiple_users_calculations(cursor, user_ids)

    write_html_to_file(cursor)

    # commit changes and close the connection
    connection.commit()
    connection.close()

    with open("last_update.json", "w") as f:
        json.dump(
            {
                "round": active_round,
                "in_play": in_play
            }, f
        )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
