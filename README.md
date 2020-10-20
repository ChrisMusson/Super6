
# Super 6
Super 6 is a football prediction game run by Sky Sports for players based in the UK and the Republic of Ireland. Every week, 6 matches are chosen and the aim is to predict the correct score for all 6 of these games. You can also join a league with friends, and gain points by either predicting the correct score (5 points), or predicting the correct result but not the correct score (2 points). The files in this repository give a database containing data for the players in your `IDs.csv` file. The `Calculations` table gives an extended league table compared to what is found on the Super 6 website, including columns such as rounds played, average points per round, variance, and how many times you were off by 1, 2, 3, etc. goals. Finally, an ASCII table representing this data is printed out to the command line. In `docs/`, I have also included an example webpage that can easily be made from this data. This webpage can be found at https://chrismusson.github.io/Super6/

# Usage
1. Clone this repository `git clone "https://github.com/ChrisMusson/Super6"`
1. Install requirements from txt file - `pip install -r requirements.txt`
1. Edit `IDs.csv` to include all the IDs you want to be in your final database. 
    1. Doing this manually, these can be found by going to your desired people's results for any round. The value for that user's user ID is the 8 digit number found in the URL.

    1. If there are lots of people in your league and you want this automated, then you can call the `get_ids.py` program to fetch all IDs in a league. The syntax to do this is `python get_IDs.py <username> <pin> <league_id>`. This will overwrite the IDs in the current `IDs.csv` file.
    
    The two user IDs that are currently in the file are my personal ID and the ID of another account I own for testing purposes. Feel free to delete both of these, they are only there to show the format of an example csv.

1. Run `main.py`. This will create a database `database.db` that has all the data from every ID you included in the `IDs.csv` file and will print out the `Calculations` table to the command line. Alternatively, you can use this database file as the datasource for a webpage, as shown in `example/`.

To change the users in your database after it has already been created, simply adding/removing the user ID from `IDs.csv` and running `main.py` again will do that for you.

If you delete your database file at any point, then running `main.py` again will automatically fix `last_update.json` for you and will give the correct league table.

# Example
Here is an example of the printed league table (with names and IDs omitted)
```+----------+------+--------+---------+--------+--------+---------------+----------+----------+----------+----------+-------------+
+----------+------+--------+---------+--------+--------+---------------+----------+----------+----------+----------+-------------+
| user_id  | name | played | results | scores | points | pts_per_round | variance | off_by_1 | off_by_2 | off_by_3 | off_by_more |
+----------+------+--------+---------+--------+--------+---------------+----------+----------+----------+----------+-------------+
| 1663XXXX | L P  |   65   |   134   |   40   |  468   |      7.20     |  17.21   |    98    |   128    |    69    |      55     |
| 1663XXXX | E R  |   66   |   152   |   31   |  459   |      6.95     |  11.53   |   109    |   138    |    70    |      48     |
| 1597XXXX | C M  |   59   |   134   |   38   |  458   |      7.76     |  16.05   |    92    |   122    |    69    |      33     |
| 1578XXXX | M J  |   60   |   133   |   32   |  426   |      7.10     |  18.49   |   100    |   120    |    59    |      49     |
| 1912XXXX | F I  |   61   |   141   |   28   |  422   |      6.92     |  11.26   |    92    |   128    |    73    |      45     |
| 1785XXXX | W C  |   59   |   125   |   23   |  365   |      6.19     |  13.20   |    94    |   117    |    67    |      53     |
| 1531XXXX | M H  |   56   |   112   |   28   |  364   |      6.50     |  14.11   |    61    |   105    |    73    |      69     |
| 1883XXXX | S W  |   42   |    81   |   34   |  332   |      7.90     |  24.85   |    68    |    79    |    49    |      22     |
| 1751XXXX | L C  |   47   |    81   |   33   |  327   |      6.96     |  16.13   |    92    |    75    |    40    |      42     |
| 1815XXXX | S C  |   53   |   101   |   23   |  317   |      5.98     |  14.17   |   107    |    80    |    78    |      30     |
| 1916XXXX | A S  |   45   |    81   |   27   |  297   |      6.60     |  19.53   |    71    |    79    |    60    |      33     |
| 1598XXXX | T S  |   40   |    88   |   18   |  266   |      6.65     |  10.23   |    85    |    59    |    49    |      29     |
| 1671XXXX | D R  |   36   |    73   |   19   |  241   |      6.69     |  11.77   |    67    |    68    |    38    |      24     |
| 1445XXXX | A C  |   33   |    68   |   15   |  211   |      6.39     |  13.69   |    53    |    72    |    38    |      20     |
+----------+------+--------+---------+--------+--------+---------------+----------+----------+----------+----------+-------------+
```
