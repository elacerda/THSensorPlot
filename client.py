import socket
import sys
import datetime
import telnetlib
import re
import sqlite3
import os

import serial
import numpy as np
import plotly.plotly as py
from plotly.graph_objs import Scatter, Figure, YAxis, Layout


########### global variables (thats suck) ###########
# TODO: build a argsparse function 
max_points = 600
sensor_title = 'THSensor v0.1'
sensor_filename_plotly = 'THSensor'
stream_ids = [ u'nht587aev1', u'o02ku0mboo' ]
db_table_name = 'THSensor'
db_filename = 'THSensor.db'
y_range = [10.1, 50.1]


def connect_serial(port, baudrate=9600):
    # Establish the connection on a specific port
    return serial.Serial(port, baudrate)


class Telnet(telnetlib.Telnet):
    def readline(self):
        return self.read_until('\n').replace('\n', '')


def connect_telnet(ip, port):
    return Telnet(ip, port)


def connect_db(dbfile):
    qry = ''

    if not os.path.isfile(dbfile):
        qry = 'CREATE TABLE %s(id INTEGER PRIMARY KEY, ' % db_table_name
        qry += 'datetime TEXT, temperature REAL, humidity REAL)'

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    if qry:
        c.execute(qry)

    return conn, c


def store_data_db(dbfile, data):
    now, T, H = data
    conn, c = connect_db(dbfile)
    qry = 'INSERT INTO %s(datetime, temperature, humidity) VALUES(?,?,?)' % db_table_name
    c.execute(qry, (now, T, H))
    conn.commit()
    conn.close()


def parse_serial_data(data, data_fmt_re):
    d = re.search(data_fmt_re, data)

    if d:
        Htuple = d.group(1,2)
        Ttuple = d.group(3,4)
        if Htuple[1] == None:
            H = np.int('%s' % Htuple[0])
        else:    
            H = np.float('%s.%s' % Htuple)
        if Ttuple[1] == None:
            T = np.int('%s' % Ttuple[0])
        else:
            T = np.float('%s.%s' % Ttuple)
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')

        if T <= 100 and 0 < H <= 100:  # This avoids T = 255, H = 255 issues of DHT11.
            return now_str, T, H
        else:
            return None
    else:
        return None


def ploty_streams(s1, s2, data):
    now, T, H = data
    print '[%s] Writing to plot.ly server...' % now
    s1.write(dict(x=now, y=T))
    s2.write(dict(x=now, y=H))
    
    
def draw_stored_data(s1, s2, dbfile):
    conn, c = connect_db(dbfile)
    qry = 'SELECT datetime, temperature, humidity from %s ORDER BY id DESC limit %d' % (db_table_name, max_points)
    c.execute(qry)
    for row in c.fetchall()[::-1]:
        ploty_streams(s1, s2, row)
    conn.close()
    
    
def main():
    try:
        addr = sys.argv[1]
        rid = sys.argv[2]
    except IndexError:
        print 'Usage: %s /dev/serial_device R_ID DHT_VER or ip:port R_ID DHT_VER' % sys.argv[0]
        sys.exit(1)

    if ':' in addr:
        ip, port = addr.split(':')
        ser = connect_telnet(ip, port)
    else:
        ser = connect_serial(addr, 9600)

    data_payload = ''

    layout = Layout(
        title=sensor_title, 
        yaxis=YAxis(
            title='Temperature (Celsius) / Humidity (%)',
            range=y_range
        ),
    )

    # Get credentials from plotly configfile.
    cr = py.get_credentials()
    trace1 = Scatter(x=[], y=[], name='temperature',
                     stream=dict(token=stream_ids[0], maxpoints=max_points))
    trace2 = Scatter(x=[], y=[], name='humidity',
                     stream=dict(token=stream_ids[1], maxpoints=max_points))
    fig = Figure(data=[trace1, trace2], layout=layout)
    py.plot(fig, filename=sensor_filename_plotly, fileopt='extend')
    s1 = py.Stream(stream_ids[0])
    s2 = py.Stream(stream_ids[1])
    s1.open()
    s2.open()

    draw_stored_data(s1, s2, db_filename)
    
    while True:
        # Read the newest output from the Arduino
        data_payload = ser.readline().strip()
        #data = parse_serial_data(data_payload, ':I%sH([0-9]+).([0-9]+)T([0-9]+).([0-9]+);' % rid)
        data = parse_serial_data(data_payload, ':I%sH([0-9]{1,3})\.?([0-9]{1,2})?T([0-9]{1,3})\.?([0-9]{1,2})?;' % rid)
        if data:
            try:
                ploty_streams(s1, s2, data)
            except socket.error, e:
                print 'Error contacting plotly server: %s' % e
            store_data_db(db_filename, data)
            print '%s end' % data_payload
        else:
            print '%s error' % data_payload


if __name__ == '__main__':
    sys.exit(main())