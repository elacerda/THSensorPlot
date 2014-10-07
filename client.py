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

    conn.commit()

    return conn, c


def store_data_db(conn, c, datetime, temperature, humidity):
    qry = 'INSERT INTO THSensor(datetime, temperature, humidity) VALUES(?,?,?)'
    c.execute(qry, (datetime, temperature, humidity))
    conn.commit()


ser = connect_serial(sys.argv[1], 9600)
conn, c = connect_db('THSensor.conn')
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
        data = re.search('H([0-9]+)T([0-9]+)', data_payload)
        now = datetime.datetime.now()
        nowStr = now.strftime('%Y-%m-%d %H:%M:%S')
        T = np.float(data.group(2))
        H = np.float(data.group(1))
        store_data_db(conn, c, nowStr, T, H)
        print '[%s] Writing to plot.ly server...' % nowStr
        s1.write(dict(x=nowStr, y=T))
        s2.write(dict(x=nowStr, y=H))
        print '%s end' % data_payload
    else:
        data_payload += rl
