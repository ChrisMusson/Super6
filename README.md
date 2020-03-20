## NOTE: Due to COVID-19, none of this will work. Super6 rounds have been suspended until further notice, likely as late as May/June.

# Super 6
Super 6 is a football prediction game run by Sky Sports for players based in the UK and the Republic of Ireland. Every week, 6 matches are chosen and the aim is to predict the correct score for all 6 of these games. You can also join a league with friends, and gain points by either predicting the correct score (5 points), or predicting the correct result but not the correct score (2 points). The files in this repository give a Google sheet with an extended league table compared to that on the Super 6 website, with extra columns such as rounds played, mean points per round, standard deviation, and how many times you were off by a certain number of goals.

# Example
An example of what a finished version of this looks like (with names omitted) can be found here: https://docs.google.com/spreadsheets/d/1eRPzH7XA67ABOfYwXKEaxw50M9_yFgPY38wNG8Ss8Nw/edit#gid=1024874317

# Usage
1. Clone this repository `git clone "https://github.com/ChrisMusson/Super6"`
1. Install requirements from txt file - `pip install -r requirements.txt`
1. Create a new project on the Google Developer Console - https://console.developers.google.com/
1. After being redirected to the project dashboard, enable APIs and services, and find and enable both the "Sheets API" and "Drive API"
1. Go to the credentials tab and create credentials > service account key.
1. Create and download the key with the service account as ‘App Engine Default’ and key type as JSON.
1. Rename this key to "creds.json" and move it to the same directory as the other files in this project.
1. Create a new google spreadsheet and rename it to something reasonable - https://sheets.new
1. Share this spreadsheet (green button, top right) with the client email located in your creds.json file.
1. Open setup.py and change the league_id and spreadsheet_name to your desired values, and username and pin to your login details.
  Note: The spreadsheet name must be the same as what you chose to call it in step 7, and the league ID can be found when looking at the current standings on the super6 website.
1. Run setup.py. This should change your new spreadsheet to a blank version of the final spreadsheet and also create one new json file that stores the IDs of all players in your league, and two new csv files 'predictions' and 'results' that are later used to populate the spreadsheet.
1. Run main.py. This will find how many rounds you have played and how many rounds have been played in the game, get the results and predictions until you are up to date, and then update your Google sheet accordingly.
