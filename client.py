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
        qry = 'CREATE TABLE THSensor(id INTEGER PRIMARY KEY, '
        qry += 'datetime TEXT, temperature REAL, humidity REAL)'

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()

    if qry:
        c.execute(qry)

    return conn, c


def store_data_db(dbfile, data):
    now, T, H = data
    conn, c = connect_db(dbfile)
    qry = 'INSERT INTO THSensor(datetime, temperature, humidity) VALUES(?,?,?)'
    c.execute(qry, (now, T, H))
    conn.commit()
    conn.close()


def parse_serial_data(data, data_fmt_re):
    d = re.search(data_fmt_re, data)

    if d:
        T = np.float(d.group(2))
        H = np.float(d.group(1))
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')

        if 0 < T <= 100 and 0 < H <= 100:  # This avoids T = 255, H = 255 issues of DHT11.
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


def main():
    try:
        addr = sys.argv[1]
    except IndexError:
        print 'Usage: %s /dev/serial_device or ip:port' % sys.argv[0]
        sys.exit(1)

    if ':' in addr:
        ip, port = addr.split(':')
        ser = connect_telnet(ip, port)
    else:
        ser = connect_serial(addr, 9600)

    data_payload = ''

    layout = Layout(
        title='THSensor v0.1',
        yaxis=YAxis(
            title='Temperature (Celsius) / Humidity (%)',
            range=[10, 50]
        ),
    )

    # Get credentials from plotly configfile.
    cr = py.get_credentials()
    trace1 = Scatter(x=[], y=[], name='temperature',
                     stream=dict(token=cr['stream_ids'][0], maxpoints=1440))
    trace2 = Scatter(x=[], y=[], name='humidity',
                     stream=dict(token=cr['stream_ids'][1], maxpoints=1440))
    fig = Figure(data=[trace1, trace2], layout=layout)
    py.plot(fig, filename='THSensor', fileopt='extend')
    s1 = py.Stream(cr['stream_ids'][0])
    s2 = py.Stream(cr['stream_ids'][1])
    s1.open()
    s2.open()

    while True:
        # Read the newest output from the Arduino
        data_payload = ser.readline().strip()
        data = parse_serial_data(data_payload, ':H([0-9]+)T([0-9]+);')
        if data:
            try:
                ploty_streams(s1, s2, data)
            except socket.error, e:
                print 'Error contacting plotly server: %s' % e
            store_data_db('THSensor.db', data)
            print '%s end' % data_payload
        else:
            print '%s error' % data_payload


if __name__ == '__main__':
    sys.exit(main())