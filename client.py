import sys
import time
import datetime
import serial
import re
import numpy as np
try:
    import plotly.plotly as py
    import plotly.tools as tls
    from plotly.graph_objs import Scatter, Data, Figure, YAxis, Layout, Font
except ImportError:
    print 'Could not import plotly python module.'
    sys.exit(2)

try:
    ser = serial.Serial(sys.argv[1], 9600) # Establish the connection on a specific port
except IndexError:
    print 'Usage: %s /dev/serial_device' % sys.argv[0]

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
       print '[%s] Writing to plot.ly server...' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       s1.write(dict(x=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), y=np.float(data.group(2))))
       s2.write(dict(x=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), y=np.float(data.group(1))))
       print "%s end" % data_payload
       time.sleep(30)
   else:
       data_payload += rl
