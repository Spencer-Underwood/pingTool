__author__ = 'Spencer Underwood'
import sqlite3
import subprocess
import sys
import re
from datetime import datetime

# REGEX strings
# Frankly speaking, I don't really "get" regex, but these appear to work.
# Matches all IPv4 addresses
ip_regex = re.compile("[0-9]+.[0-9]+.[0-9]+.[0-9]+")
# Matches the time string in windows ping utility
time_regex = re.compile('time=[0-9]+ms|time<[0-9]+ms')

# DB Connection
# Create a connection object to the database file
connection = sqlite3.connect("pings.sqlite")
# Creates a cursor object to execute SQL statements such as SELET or INSERT
cursor = connection.cursor()

# Holds all of the process objects
# TODO: Determine if worthwhile to create custom Process class for managing sub-processes
processes = []


# Searches the database to see if there already exists a host with a given IPV4 address
# If not, create one and add it to the database.
# Returns the ID for either the newly created host, or the pre-existing host address.
def get_host(arg):
    # Checks to see if host exists in DB
    cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [arg])
    if cursor.fetchone() == None:
        # If it doesn't, create one and add it into the DB
        cursor.execute("INSERT INTO hosts VALUES (?)", [arg])
        connection.commit()
    # Select the host_id for the ip address and return it
    cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [arg])
    return cursor.fetchone()

# Parses the string output of the subprocesses and either ignores it or inserts it into the DB
# Unfortunately I haven't thought of a cleaner solution to avoid having to pass the host_id value here.
def parse_line(line, host_id):
    # Gets a datetime object for this exact moment of time
    now = datetime.now()
    # If there is a pattern in the string which matches both the IPV4 regex and time regex,
    # insert it into the database
    if (ip_regex.search(line) and time_regex.search(line) ):
        # Gets the time substring out of the string passed to this method
        ping_time = line[time_regex.search(line).start():time_regex.search(line).end()][5:-2]
        insert_into_db(host_id, ping_time, now)
    # If the request timed out, insert a record with 'None' in the time field/
    elif "Request timed out." in line:
        insert_into_db(host_id, None, now)


# Simple convience method to insert a record into the database.
# Inserts the provided values into the pings table.
def insert_into_db(host_id, ping_time, date_time):
    cursor.execute("INSERT INTO pings VALUES (?,?,?)", [host_id, ping_time, unix_time(date_time)])
    connection.commit()


# Attempts to free resources by killing all processes AND close the database connection.
# Provided by Mark Ransom at stack overflow here: http://stackoverflow.com/questions/7852855/how-to-convert-a-python-datetime-object-to-seconds
def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

# Stops all running pings and release database resources before shutting down.
def tear_down():
    # Kill each subprocess opened in the main thread.
    for process in processes:
        process.kill()
    # Release DB resources
    cursor.close()
    connection.close()


if __name__ == "__main__":
    # Creates the tables in the database if they do not exist already.
    cursor.execute("CREATE TABLE IF NOT EXISTS hosts( address TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS pings(host_id INT, time INT, datetime DATETIME)")

    # Attempts to open the last_opeened.txt file and read the most recent date time stamp in it.
    try:
        # Opens the text file and closes it as soon as it leaves this code block to avoid resource leak
        with open("last_opened.txt", "r") as file:
            # Creates a date timestamp
            date_thing = datetime.strptime(file.readline(), "%Y-%m-%d %H:%M:%S")
            print "Last ran on date: ", date_thing
    # If the file doesn't exist, inform the user
    except IOError:
        print "Application has never run before"

    # Pretty much the same as before, but writes a date timestamp into the file instead of reads
    try:
        with open("last_opened.txt", "w") as file:
            file.write(str(datetime.today().strftime("%Y-%m-%d %H:%M:%S")))
    except IOError:
        # I don't care if there's a file I/O problem since it doesn't affect anything
        # Just don't crash
        pass

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