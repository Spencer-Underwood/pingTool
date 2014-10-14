__author__ = 'Spencer'
import sqlite3
import subprocess
import sys
import re
import datetime

# REGEX
ip_regex   = re.compile("[0-9]+.[0-9]+.[0-9]+.[0-9]+")
time_regex = re.compile('time=[0-9]+ms')

# DB STUFF
connection=sqlite3.connect("pings.sqlite")
cursor = connection.cursor()

# PING STUFF
cmd = "ping 8.8.8.8 -t"
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# TODO: Add support for pinging multiple hosts

def parse_line(line):
    now = datetime.datetime.now()
    if (ip_regex.search(line) and time_regex.search(line) ):
        ping_time = line[time_regex.search(line).start():time_regex.search(line).end()][5:-2]
        insert_into_db(ping_time,now)
    elif "Request timed out." in line:
        insert_into_db(None,now)


def insert_into_db(ping_time, date_time):
    cursor.execute("INSERT INTO pings VALUES (?,?)", [ping_time, unix_time(date_time) ])
    connection.commit()


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def tear_down():
    process.terminate()
    cursor.close()
    connection.close()
    sys.exit()

if __name__ == "__main__":
    cursor.execute("CREATE TABLE IF NOT EXISTS pings(time INT, datetime DATETIME)")
    try:
        for line in iter(process.stdout.readline, ''):
            parse_line(line)
            print line[:-1]
    except KeyboardInterrupt:
        tear_down()
