# Super 6
Super 6 is a football prediction game run by Sky Sports for players based in the UK and the Republic of Ireland. Every week, 6 matches are chosen and the aim is to predict the correct score for all 6 of these games. You can also join a league with friends, and gain points by either predicting the correct score (5 points), or predicting the correct result but not the correct score (2 points). The files in this repository give a database containing all data for the players in your `IDs.csv` file. The `Calculations` table gives an extended league table compared to what is found on the Super 6 website, including columns such as rounds played, average points per round, and how many times you were off by 1, 2, 3, etc. goals. Finally, an ASCII table representing this data is printed out to the command line.

# Usage
1. Clone this repository `git clone "https://github.com/ChrisMusson/Super6"`
2. Install requirements from txt file - `pip install -r requirements.txt`
3. Edit `IDs.csv` to include all the IDs you want to be in your final database. These can be found by going to your desired person's results for any round. The value for that user's user ID is the 8 digit number found in the URL. The two user IDs that are currently in `IDs.csv` are my personal ID and the ID of another account I own for testing purposes. Feel free to delete both of these, they are only there to show the format of an example csv.
4. Run main.py - `python main.py` or `python3 main.py`. This will create a database `database.db` that has all the data from every ID you included in the `IDs.csv` file and will print out the `Calculations` table to the command line.