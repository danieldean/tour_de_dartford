#!/usr/bin/python3

#
# tour_de_dartford
#
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
#
# Licensed under The MIT License a copy of which you should have
# received. If not, see:
#
# http://opensource.org/licenses/MIT
#

import requests
import json
import sqlite3
import datetime
import schedule
import time

club = "48449"


def seconds_to_time(seconds):
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60
    return hours, minutes, seconds


def fetch_leaderboard():

    db = sqlite3.connect('leaderboard.db')
    c = db.cursor()

    r = requests.get('https://www.strava.com/clubs/' + club + "/leaderboard",
                     headers={'accept': 'text/javascript', 'x-requested-with': 'XMLHttpRequest'})

    if r.status_code == 200:

        leaderboard = json.loads(r.text)

        for athlete in leaderboard['data']:

            c.execute('INSERT OR IGNORE INTO athletes VALUES (?,?,?,?,?)', (athlete['athlete_id'],
                                                                            athlete['athlete_firstname'],
                                                                            athlete['athlete_lastname'],
                                                                            0,
                                                                            0))

            mondays_date = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())

            ride_time_total = c.execute('SELECT SUM(ride_time) FROM daily_totals WHERE athlete_id=? AND date>=?',
                                        (athlete['athlete_id'], mondays_date)).fetchone()[0]
            if ride_time_total:
                ride_time = athlete['ride_time'] - ride_time_total
            else:
                ride_time = athlete['ride_time']

            run_time_total = c.execute('SELECT SUM(run_time) FROM daily_totals WHERE athlete_id=? AND date>=?',
                                       (athlete['athlete_id'], mondays_date)).fetchone()[0]
            if run_time_total:
                run_time = athlete['run_time'] - run_time_total
            else:
                run_time = athlete['run_time']

            swim_time_total = c.execute('SELECT SUM(swim_time) FROM daily_totals WHERE athlete_id=? AND date>=?',
                                        (athlete['athlete_id'], mondays_date)).fetchone()[0]
            if swim_time_total:
                swim_time = athlete['swim_time'] - swim_time_total
            else:
                swim_time = athlete['swim_time']

            total_time_total = c.execute('SELECT SUM(total_time) FROM daily_totals WHERE athlete_id=? AND date>=?',
                                         (athlete['athlete_id'], mondays_date)).fetchone()[0]
            if total_time_total:
                total_time = athlete['moving_time'] - total_time_total
            else:
                total_time = athlete['moving_time']

            c.execute('INSERT INTO daily_totals VALUES (?,?,?,?,?,?)', (athlete['athlete_id'],
                                                                        datetime.date.today(),
                                                                        ride_time,
                                                                        run_time,
                                                                        swim_time,
                                                                        total_time))

        db.commit()

    else:
        print(str(r.status_code) + " occurred whilst whilst making the request.")

    db.close()


def main():

    db = sqlite3.connect('leaderboard.db')
    c = db.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS athletes ('
              'athlete_id NUMERIC, '
              'firstname TEXT, '
              'lastname TEXT, '
              'eliminated NUMERIC, '
              'opt_out NUMERIC,'
              'UNIQUE(athlete_id))')
    c.execute('CREATE TABLE IF NOT EXISTS daily_totals ('
              'athlete_id NUMERIC, '
              'date TEXT, '
              'ride_time NUMERIC, '
              'run_time NUMERIC, '
              'swim_time NUMERIC, '
              'total_time NUMERIC)')
    db.commit()
    db.close()

    schedule.every().day.at("23:55").do(fetch_leaderboard)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
