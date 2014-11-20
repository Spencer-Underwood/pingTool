__author__ = 'Spencer Underwood'
import sqlite3
import subprocess
import time
import sys
import re
from datetime import datetime
import threading

# REGEX strings
IP_REGEX = re.compile("[0-9]+.[0-9]+.[0-9]+.[0-9]+")
TIME_REGEX = re.compile('time=[0-9]+ms|time<[0-9]+ms')

#A constant name for the database name. Edit it here once instead of many places throughout the code.
DB_FILE_NAME = "pings.sqlite"

#Sets up a pinger object to ping a remote network host non stop and store the results in a sqlite database.
#Extends threading.Thread to handle multithreading well.
class pinger(threading.Thread):

    #Searches the database to see if an address has a related host. If it doesn't create a new one and return it.
    def get_host(self, address):
        host = None
        #Connect to the database and release the connection as soon as it's done
        with sqlite3.connect(DB_FILE_NAME) as connection:
            # Creates a cursor to execute sql statements with
            cursor = connection.cursor()
            # Checks to see if a host exists for an address already
            cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [address])
            if cursor.fetchone() == None:
                # If it doesn't, create one and add it into the DB
                cursor.execute("INSERT INTO hosts VALUES (?)", [address])
                connection.commit()
            # Select the host_id for the ip address and return it
            cursor.execute("SELECT ROWID FROM hosts WHERE address = ?", [address])
            host = cursor.fetchone()[0]
            #closes the cursor and returns the host address
            cursor.close()
        return host

    # Signals the thread to kill itself and closes any outstanding resources
    def shutdown(self):
        self.__ping_process.kill()
        self.exit.set()
        # Lets the user know that the subprocess was killed correctly
        print self.__str__() + " killed"

    # Reads the string provided and returns any meaningful information from it.
    # If the packet was dropped or otherwise malformed, returns None.
    def parse_line(self, line):
        now = (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()
        # If the string matches the IP_REGEX and TIME_REGEX patterns.
        if (IP_REGEX.search(line) and TIME_REGEX.search(line) ):
            # Gets the time substring out of the string passed to this method
            ping_time = line[TIME_REGEX.search(line).start():TIME_REGEX.search(line).end()][5:-2]
            return {"time": ping_time, "date": now}
        # If the request timed out, insert a record with 'None' in the time field/
        elif "Request timed out." in line:
            return {"time": None, "date": now}
        elif "Pinging " in line:
            return {"time": None, "date": now}

    # Self exploratory,
    def insert_into_db(self, host_id, ping_time, date_time):
        with sqlite3.connect(DB_FILE_NAME) as connection:
            cursor = connection.cursor()
            # Inserts the data into the database
            cursor.execute("INSERT INTO pings VALUES (?,?,?)", [host_id, ping_time, date_time])
            connection.commit()
            cursor.close()

    # THIS METHOD BLOCKS, ONLY CALL ON NEW THREAD
    #
    def run(self):
        # First line always appears t obe a blank lane and is thus useless
        self.__ping_process.stdout.readline()
        # Print the second line. It's also not a ping response, so useless for us
        print self.__ping_process.stdout.readline()
        # Loop forever reading and parsing the results from the pinging subprocess
        while not self.exit.is_set():
            # Last character is a newline, we don't want it.
            line = self.__ping_process.stdout.readline()[0:-1]
            # prints the pings to the console
            print line
            # Parse and insert the line into the database
            parse_results = self.parse_line(line)
            if parse_results is not None:
                self.insert_into_db(self.host, parse_results.get("time"), parse_results.get("date"))

    # Initializes the pinger object
    def __init__(self, address):
        # Gets the host ID for this object from the database
        self.host = self.get_host(address)
        # Starts pinging the provided network host in a new subprocess
        self.__ping_process = subprocess.Popen("ping {0} -t".format(address), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        # save the process ID of this subprocess just in case it matters
        self.pid = self.__ping_process.pid
        # Sets up the exit flag to kill this thread.
        self.exit = threading.Event()
        # Sets up any init that the super class needs/
        threading.Thread.__init__(self)

    def __str__(self):
        return ("<Pinger| Host #:" + str(self.host) + ">")

# Purely proof of concept code
class MyCollection(object):
    def __init__(self):
        self._data = [4, 8, 16, 32, 64, 129]

    def __iter__(self):
        for elem in self._data:
            yield elem



if __name__ == "__main__":
    # Create database tables if they don't exist already
    with sqlite3.connect("pings.sqlite") as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS hosts( address TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS pings(host_id INT, time INT, datetime DATETIME)")
        cursor.close()
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

    pinger_objects = []
    # If any of the command line arguments are an IP address, create a new process to ping that host
    for arg in sys.argv[1:]:
        #Checks if argument is a formatted like an IPv4 address or not
        if IP_REGEX.search(arg):
            new_pinger = pinger(arg)
            new_pinger.start()
            pinger_objects.append(new_pinger)

    test = MyCollection()
    for element in test:
        print element

    # Sorts the list of pigner objects by PID
    pinger_objects.sort()
    for p in pinger_objects:
        print p.pid

    # Since the list of ping objects has been started, just wait until the user kills the program/
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Kill each thread when there is a keyboard interrupt signal.
        for p in pinger_objects:
            p.shutdown()