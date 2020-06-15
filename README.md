# Super 6
Super 6 is a football prediction game run by Sky Sports for players based in the UK and the Republic of Ireland. Every week, 6 matches are chosen and the aim is to predict the correct score for all 6 of these games. You can also join a league with friends, and gain points by either predicting the correct score (5 points), or predicting the correct result but not the correct score (2 points). The files in this repository give a database with an extended league table compared to that on the Super 6 website, with extra columns such as rounds played, mean points per round, how many times you were off by a certain number of goals.

# Usage
1. Clone this repository `git clone "https://github.com/ChrisMusson/Super6"`
2. Install requirements from txt file - `pip install -r requirements.txt`
3. Edit `IDs.csv` to include all the IDs you want to be in your final database. The two that are currently in there are my personal ID and the ID of another account I own for testing purposes. Feel free to delete both of these.
4. Run main.py - `python main.py` or `python3 main.py`. This will create a database `database.db` that has all the data from every ID you included in the `IDs.csv` file.