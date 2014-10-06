import sys
import time
import datetime
import serial
import re
import numpy as np
import sqlite3
import os
try:
    import plotly.plotly as py
    import plotly.tools as tls
    from plotly.graph_objs import Scatter, Data, Figure, YAxis, Layout, Font
except ImportError:
    print 'Could not import plotly python module.'
    sys.exit(2)

def connectSerial(port, baudrate = 9600):
    try:
        return serial.Serial(port, baudrate) # Establish the connection on a specific port
    except IndexError:
        print 'Usage: %s /dev/serial_device' % sys.argv[0]
        
def connectDB(dbfile):
    createSQL = ''
    if not os.path.isfile(dbfile):
        createSQL = '''
        CREATE TABLE THSensor(id INTEGER PRIMARY KEY, datetime TEXT, temperature REAL, humidity REAL)
        '''        
    db = sqlite3.connect(dbfile)
    c = db.cursor()
    if createSQL:
        c.execute(createSQL)
    return db, c

def storeDataDB(db, cursor, datetime, temperature, humidity):
    cursor.execute('''INSERT INTO THSensor(datetime, temperature, humidity) VALUES(?,?,?)''', (datetime, temperature, humidity))
    db.commit()

ser = connectSerial(sys.argv[1], 9600)
db, cursor = connectDB('THSensor.db')
data_payload = "";

layout = Layout(
    title='THSensor v0.1',
    yaxis=YAxis(
        title='Temperature (Celsius) / Humidity (%)',
        range=[10, 50]
    ),
)

cr = py.get_credentials() # Get credentials from plotly configfile.

trace1 = Scatter(x=[], y=[], name='temperature', stream=dict(token=cr['stream_ids'][0], maxpoints=1440)) #, xaxis='x1')
trace2 = Scatter(x=[], y=[], name='humidity', stream=dict(token=cr['stream_ids'][1], maxpoints=1440)) #, xaxis='x2')
fig = Figure(data=[trace1, trace2], layout=layout)
py.plot(fig, filename='THSensor', fileopt='extend')
s1 = py.Stream(cr['stream_ids'][0])
s2 = py.Stream(cr['stream_ids'][1])
s1.open()
s2.open()

while True:
   rl = ser.readline().strip() # Read the newest output from the Arduino

   if rl == ":":
       data_payload = "";
   elif rl == ";":
       data = re.search('H([0-9]+)T([0-9]+)', data_payload)
       now = datetime.datetime.now()
       nowStr = now.strftime('%Y-%m-%d %H:%M:%S')
       T = np.float(data.group(2))
       H = np.float(data.group(1))
       storeDataDB(db, cursor, nowStr, T, H)
       print '[%s] Writing to plot.ly server...' % nowStr 
       s1.write(dict(x=nowStr, y=T))
       s2.write(dict(x=nowStr, y=H))
       print "%s end" % data_payload
   else:
       data_payload += rl
