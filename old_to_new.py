__author__ = 'Spencer'
import sqlite3
import datetime
connection=sqlite3.connect("pings.sqlite")
cursor = connection.cursor()



def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds())

cursor.execute("SELECT rowid, datetime FROM pings")
results = cursor.fetchall()
for row in results:
    rowid =  int(row[0])
    new_time_stamp = unix_time(datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"))
    # print rowid
    # print new_time_stamp
    # cursor.execute("SELECT * FROM pings WHERE rowid ="+rowid.__str__())
    # print cursor.fetchone()
    cursor.execute("UPDATE pings SET datetime=? WHERE rowid=?;", (new_time_stamp, rowid))
