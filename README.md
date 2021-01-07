# Tour de Dartford

Script to automatically collect club leaderboard data from Strava and 
calculate a daily as opposed to weekly total for each athlete. Doing 
this enables tracking on a daily, weekly, monthly or yearly period to 
set longer term challenges.

At 23:55 Strava is queried for the leaderboard data via an XMLHttpRequest 
in the same manner its own website does without any need to authenticate 
or sign up for their API. The response is JSON.

The JSON response is inserted an SQLite3 database. If the day is not a 
Monday the database is first queried for the running weekly total for 
each athlete and this is then subtracted to obtain a daily figure.

To provide a friendly summary of the data the script also creates and 
saves an HTML table which is committed to another repo which contains a 
statically hosted webpage. This webpage dynamically loads the table which 
is updated daily at 23:56.

See [tdd](https://github.com/danieldean/tdd) for the static webpage.
