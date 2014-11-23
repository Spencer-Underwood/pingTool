__author__ = 'Spencer'
import sys
from datetime import timedelta
import datetime
import time
import pygal
from pygal.style import CleanStyle
import sqlite3

# DB Connection
# Create a connection object to the database file
connection = sqlite3.connect("pings.sqlite")
# Creates a cursor object to execute SQL statements such as SELET or INSERT
cursor = connection.cursor()

# Time Stamps
# convenience variables referring to specific points of time in the past
today = datetime.datetime.now() - timedelta(days=0)
yesterday = today - timedelta(days=1)
last_week = today - timedelta(days=7)

# Creates the average_ping_per_hour line graph
def average_ping_per_hour():
    #Creates the chart object with the style of CleanStyle
    bar_chart = pygal.Line(style=CleanStyle)
    bar_chart.title = "Average ping (ms) per hour"
    bar_chart.x_labels = map(str, range(0, 24))

    bar_chart.add('All Time', _get_average_ping_from_time(datetime.datetime.min))
    # bar_chart.add('Last Week', _get_average_ping_from_time(last_week))
    bar_chart.add('Last Day', _get_average_ping_from_time(yesterday))

    bar_chart.render_to_file("bar_chart.svg")


# Internal use only. Paramter passed MUST be a datetime object.
# Returns a list of 24 integers with the average ping for the given hour/
def _get_average_ping_from_time(datetime):
    # Get all ping objects from the database between the given datetime and today
    cursor.execute("SELECT * FROM pings WHERE datetime BETWEEN ? AND ?", [time.mktime(datetime.timetuple()), time.mktime(datetime.today().timetuple())])
    # Instantiate the two lists used
    hour_summ = [0 for x in range(0, 24)]
    hour_count = [0 for x in range(0, 24)]

    # Sums all the pings in each hour
    for row in cursor:
        date = datetime.fromtimestamp(row[2])
        if row[1] is not None:
            hour_summ[date.hour]+= row[1]
            hour_count[date.hour]+=1

    # Calculates the average ping for each hour
    for i in range(0, 24):
        try:
            hour_summ[i] = hour_summ[i] / hour_count[i]
        except ZeroDivisionError:
            # If no pings for a given hour, use 0 as the default value
            hour_summ[i] = 0
    return hour_summ


# DEPRECATED, DO NOT USE
def to_textfile():
    cursor.execute("SELECT * FROM pings ORDER BY datetime(datetime) DESC")
    with open("Ping_Results.txt", "w") as text_file:
        for row in cursor:
            try:
                time = int(row[0]).__str__() + "ms"
            except TypeError:
                time = "N/A"
            text_file.write(time.__str__() + "," + row[1] + "\n")

# Free system resources
def quit():
    cursor.close()
    connection.close()
    sys.exit()

# Creates the graph and then quits.
# TODO: Implement sys args to control main method
if __name__ == "__main__":
    average_ping_per_hour()
    quit()
    # print "blah blah blah ping tracker app stuff"
    # app_main_loop = True
    # print "Supported options: box chart, average ping, quit"
    #
    # try:
    #     while (app_main_loop == True):
    #         user_input = raw_input('Type an option: ').lower()
    #
    #         if user_input == "quit":
    #             quit()
    #         elif user_input == "average ping":
    #             average_ping_per_hour()
    #         elif user_input == "textfile":
    #             to_textfile()
    #         else:
    #             print "Option not supported, please try again."
    #             print  "Supported options are: box chart, picture, quit"
    # except KeyboardInterrupt:
    #     quit()
    #
    # print "Goodbye"