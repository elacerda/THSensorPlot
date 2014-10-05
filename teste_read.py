#!/usr/bin/python
from time import sleep
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200) # Establish the connection on a specific port
counter = 32 # Below 32 everything in ASCII is gibberish
data_payload = "";
while True:
   rl = ser.readline().strip() # Read the newest output from the Arduino

   if rl == ":":
      data_payload = "";
   elif rl == ";":
      print "%s end" % data_payload
   else:
      data_payload += rl
