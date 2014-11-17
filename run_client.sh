#!/bin/bash
DEVICE=localhost:4420 #/dev/ttyUSB0
DIR=$PWD
RID=10 #or 42
### client script
cd $DIR
echo "Running chat_server..."
twistd -y serial_server/serial_chat_server.py
sleep 3
echo "Running THSensorPlot in background..."
screen -dmS THSensor python client.py $DEVICE $RID
