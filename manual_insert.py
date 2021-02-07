#!/usr/bin/python3

#
# manual_insert
#
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
#
# Licensed under The MIT License a copy of which you should have
# received. If not, see:
#
# http://opensource.org/licenses/MIT
#

import sqlite3

# Format should be (athlete_id, 'YYYY-MM-DD', ride_time, run_time, swim_time, total_time)
# All of the times should be in seconds. Use the spreadsheet to construct the tuple for you.
records = []


def main():
    db = sqlite3.connect('leaderboard.db')
    c = db.cursor()
    c.executemany('INSERT INTO daily_totals VALUES (?,?,?,?,?,?)', records)
    db.commit()


if __name__ == '__main__':
    main()
