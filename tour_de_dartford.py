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
from git import Repo

repo_path = r'tdd/.git'
club = "48449"


def git_push(commit_message):
    repo = Repo(repo_path)
    repo.git.add(all=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()


def create_table():

    db = sqlite3.connect('leaderboard.db')
    c = db.cursor()

    leaderboard = c.execute('SELECT athletes.athlete_id, firstname, lastname, SUM(ride_time), SUM(run_time), '
                            'SUM(swim_time), SUM(total_time) FROM athletes INNER JOIN daily_totals ON '
                            'athletes.athlete_id=daily_totals.athlete_id WHERE strftime("%m", date)=? GROUP BY '
                            'athletes.athlete_id ORDER BY SUM(total_time) DESC',
                            (datetime.date.today().strftime('%m'), ))

    table = '<div class="first">' + datetime.date.today().strftime('%B') + '</div>\n'
    table += '<table>\n'
    table += '    <thead>\n'
    table += '        <tr class="second">\n'
    table += '            <th>Rank</th>\n'
    table += '            <th>Athlete</th>\n'
    table += '            <th>Ride Time</th>\n'
    table += '            <th>Run Time</th>\n'
    table += '            <th>Swim Time</th>\n'
    table += '            <th>Total Time</th>\n'
    table += '        </tr>\n'
    table += '    </thead>\n'
    table += '    <tbody>\n'

    rank = 1

    for athlete in leaderboard:

        table += '        <tr>\n'
        table += '            <td>' + str(rank) + '</td>\n'
        table += '            <td>' + athlete[1] + ' ' + athlete[2] + '</td>\n'
        table += '            <td>' + str(datetime.timedelta(seconds=athlete[3])) + '</td>\n'
        table += '            <td>' + str(datetime.timedelta(seconds=athlete[4])) + '</td>\n'
        table += '            <td>' + str(datetime.timedelta(seconds=athlete[5])) + '</td>\n'
        table += '            <td>' + str(datetime.timedelta(seconds=athlete[6])) + '</td>\n'
        table += '        </tr>\n'

        rank += 1

    table += '    </tbody>\n'
    table += '</table>'

    db.close()

    f = open('tdd/table-' + datetime.date.today().strftime('%b').lower() + '.html', 'wt')

    f.write(table)

    f.close()

    git_push('Stats update: ' + str(datetime.date.today()))


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
    schedule.every().day.at("23:56").do(create_table)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
