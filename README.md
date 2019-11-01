# Super6
Super 6 is a football prediction game run by Sky Sports for players based in the UK and the Republic of Ireland. Every week, 6 matches are chosen and the aim is to predict the correct score for all 6 of these games. You can also join a league with friends, and gain points by either predicting the correct score (5 points), or predicting the correct result but not the correct score (2 points). The files in this repository give a google sheet with an extended league table compared to that on the Super 6 website, with extra columns such as rounds played, mean points per round, standard deviation, and how many times you were off by one goal.

# Example
An example of what an up-to-date version of this looks like with formatting can be found here: https://docs.google.com/spreadsheets/d/1eRPzH7XA67ABOfYwXKEaxw50M9_yFgPY38wNG8Ss8Nw/edit#gid=1024874317

# Requirements:
A valid Google account

Requests

Beautiful Soup

pygsheets

pandas

# Usage
1. Install Requests, Beautiful Soup, pygsheets, and pandas.
2. Go to the Google Developer Console and create a new project - https://console.developers.google.com/
3. After being redirected to the project dashboard, click on enable APIs and services, and find and enable both the "Sheets API" and "Drive API"
4. Go to the credentials tab and create credentials > service account key.
5. With the service account as ‘App Engine Default’ and key type as JSON, create your key and download it.
6. Rename this key to "creds.json" and move it to the same directory as the other files in this project.
7. Create a new google spreadsheet and rename it to something reasonable - https://sheets.new
8. Share this spreadsheet with the client email located in you creds.json file.
9. Open setup.py and change the league_id and spreadsheet_name to your desired values, and username and pin to your login details.
  Note: The spreadsheet name must match with that you chose to call it in step 7, and the league ID can be found when looking at the current standings on the super6 website.
10. Run setup.py. This should change your new spreadsheet to a blank version of the final spreadsheet and also create one new json file that stores the IDs of all players in your league, and two new csv files 'predictions' and 'results' that are later used to populate the spreadsheet.
11. Run main.py. This will find how many rounds you have played and how many round have been played in the game, and get the results and predictions until you are up to date.
