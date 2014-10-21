__author__ = 'Spencer'
import sqlite3
import subprocess
import sys
import re
from datetime import datetime

# REGEX strings
ip_regex = re.compile("[0-9]+.[0-9]+.[0-9]+.[0-9]+")
time_regex = re.compile('time=[0-9]+ms|time<[0-9]+ms')

# DB Connection
connection = sqlite3.connect("pings.sqlite")
cursor = connection.cursor()

# Holds all of the process objects
# TODO: Determine if worthwhile to create Process object for
processes = []


def init():
    cursor.execute("CREATE TABLE IF NOT EXISTS hosts( address TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS pings(host_id INT, time INT, datetime DATETIME)")

    try:
        with open("last_opened.txt", "r") as file:
            date_thing = datetime.strptime(file.readline(), "%Y-%m-%d %H:%M:%S")
            print "Last ran on date: ", date_thing

    except IOError:
        print "Application has never run before"

    try:
        with open("last_opened.txt", "w") as file:
            file.write(str(datetime.today().strftime("%Y-%m-%d %H:%M:%S")))
    except IOError:
        print "Application has never run before"



# TODO: Add comments later
def get_host(arg):
    cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [arg])
    if cursor.fetchone() == None:
        cursor.execute("INSERT INTO hosts VALUES (?)", [arg])
        connection.commit()
    cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [arg])
    return cursor.fetchone()


# TODO: Add comments
def parse_line(line, host_id):
    now = datetime.now()
    if (ip_regex.search(line) and time_regex.search(line) ):
        ping_time = line[time_regex.search(line).start():time_regex.search(line).end()][5:-2]
        insert_into_db(host_id, ping_time, now)
    elif "Request timed out." in line:
        insert_into_db(host_id, None, now)


#TODO: Add comments
def insert_into_db(host_id, ping_time, date_time):
    cursor.execute("INSERT INTO pings VALUES (?,?,?)", [host_id, ping_time, unix_time(date_time)])
    connection.commit()


#TODO: Add comments
def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


# Attempts to free resources by killing all processes AND close the database connection.
def tear_down():
    for process in processes:
        process.kill()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    init()  # creates the database structure

    #If any of the command line arguments are an IP address, create a new process to ping that host
    for arg in sys.argv[1:]:
        if ip_regex.search(arg):  #Checks if argument is a formatted like an IPv4 address or not
            #Create new subprocess which pings the provided host indefinitely.
            p = subprocess.Popen("ping {0} -t".format(arg), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.host_id = get_host(arg)[0]  #Attach the host IP-Address to the subprocess object.
            processes.append(p)

    try:
        while (True):  #Do this FOREVER
            for process in processes:  #
                line = process.stdout.readline()
                parse_line(line, process.host_id)
                print line[0:-1]

    except KeyboardInterrupt:  # Shut down application when user quits with control-C
        tear_down()  #free up resources used before shutting donw.
        sys.exit()  #shut down