# Super6
Gives an extended league table view in google sheets for a specified super 6 league

# Example
An example of what an up-to-date version of this looks like with formatting can be found here: https://docs.google.com/spreadsheets/d/1eRPzH7XA67ABOfYwXKEaxw50M9_yFgPY38wNG8Ss8Nw/edit#gid=1024874317

# Requirements:
A valid Google account

Selenium

pygsheets

pandas

# Usage
1. Install Selenium, pygsheets, and pandas. Downlaod the latest version of chromedriver if necessary and put it in the same directory as the other files in this project - https://chromedriver.chromium.org/downloads
2. Go to the Google Developer Console and create a new project - https://console.developers.google.com/
3. After being redirected to the project dashboard, click on enable APIs and services, and find and enable both the "Sheets API" and "Drive API"
4. Go to the credentials tab and create credentials > service account key.
5. With the service account as ‘App Engine Default’ and key type as JSON, create your key and download it.
6. Rename this key to "creds.json" and move it to the same directory as the other files in this project.
7. Create a new google spreadsheet and rename it to something reasonable - https://sheets.new
8. Share this spreadsheet with the client email located in you creds.json file.
9. Open setup.py and change the league_id and spreadsheet_name to your desired values, and username and pin to any correct login details.
  Note: The spreadsheet name must match with that you chose to call it in step 7, and the league ID can be found when looking at the current standings on the super6 website.
10. Run setup.py. This should change your new spreadsheet to a blank version of the final spreadsheet and also create one new json file that stores the IDs of all players in your league, and two new csv files 'predictions' and 'results' that are later used to populate the spreadsheet.
11. Run main.py with your desired start and end rounds. If it is your first time running main.py, you will likely want to run it as main(1,x), where x is the last completed round. If your spreadsheet is already populated and you only want to add one round, then simply running it as main(x) will work.

It should be noted that the completed spreadsheet has no formatting attached to it, however adding some will not break anything.
