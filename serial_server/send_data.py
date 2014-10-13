# telnet program example
import socket, select, string, sys

import serial


#main function
if __name__ == "__main__":
     
    if(len(sys.argv) < 5) :
        print 'Usage : python %s hostname port tty baud' % sys.argv[0]
        print 'Example : python %s localhost 4420 /dev/ttyUSB0 9600' % sys.argv[0]
        sys.exit()
     
    host = sys.argv[1]
    port = int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    tty = sys.argv[3]
    baud = sys.argv[4]
    ser = serial.Serial(tty, baud)
     
    # connect to remote host
    try :
        s.connect((host, port))
    except :
        print 'Unable to connect'
        sys.exit()
     
    print 'Connected to remote host'
    
    data_payload = ''
    while True:
       rl = ser.readline() # Read the newest output from the Arduino
       s.sendall(rl)
