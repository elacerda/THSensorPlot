import sys
import datetime
import serial
import re
import numpy as np
import sqlite3
import os
try:
    import plotly.plotly as py
    from plotly.graph_objs import Scatter, Figure, YAxis, Layout
except ImportError:
    print 'Could not import plotly python module.'
    sys.exit(2)


def connect_serial(port, baudrate=9600):
    try:
        # Establish the connection on a specific port
        s = serial.Serial(port, baudrate)
    except IndexError:
        print 'Usage: %s /dev/serial_device' % sys.argv[0]

    return s


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
    print now, T, H
    conn, c = connect_db(dbfile)
    qry = 'INSERT INTO THSensor(datetime, temperature, humidity) VALUES(?,?,?)'
    print qry
    c.execute(qry, (now, T, H))
    conn.commit()
    conn.close()


def parse_serial_data(data, data_fmt_re):
    d = re.search(data_fmt_re, data)
    T = np.float(d.group(2))
    H = np.float(d.group(1))
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    return now_str, T, H


def ploty_streams(s1, s2, data):
    now, T, H = data
    print '[%s] Writing to plot.ly server...' % now
    s1.write(dict(x=now, y=T))
    s2.write(dict(x=now, y=H))
    print '%s end' % data_payload


ser = connect_serial(sys.argv[1], 9600)
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
    rl = ser.readline().strip()

    if rl == ':':
        data_payload = ''
    elif rl == ';':
        data = parse_serial_data(data_payload, 'H([0-9]+)T([0-9]+)')
        ploty_streams(s1, s2, data)
        store_data_db('THSensor.db', data)
    else:
        data_payload += rl
