/*
  Telnet client
 
 This sketch connects to a a telnet server using an Arduino Wiznet
 Ethernet shield.  You'll need a telnet server  to test this with.
 Processing's ChatServer example (part of the network library) works
 well, running on port 10002. It can be found as part of the examples in
 the Processing application, available at http://processing.org/
 
 Circuit:
 * Ethernet shield attached to pins 10, 11, 12, 13
 
 created 14 Sep 2010
 modified 9 Apr 2012
 by Tom Igoe

 adapted to retransmit 433Mhz signals over ethernet 
 by W. Schoenell - 2014
 
 */

#include <SPI.h>
#include <Ethernet.h>

#include <Wire.h>
#include <VirtualWire.h>
#include <sSerial.h>


// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = {  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192,168,1,177);

// Enter the IP address of the server you're connecting to:
IPAddress server(192,168,1,128); 

// Initialize the Ethernet client library
// with the IP address and port of the server 
// that you want to connect to (port 23 is default for telnet;
// if you're using Processing's ChatServer, use  port 10002):
EthernetClient client;

void telnet_connect() {
	// if you get a connection, report back via serial:
	if (client.connect(server, 4420))
		Serial.println("connected");
	else
	// if you didn't get a connection to the server:
		Serial.println("connection failed");
}

void setup() {
  // start the Ethernet connection:
  Ethernet.begin(mac, ip);  // without ip it tries by dhcp
  // Open serial communications and wait for port to open:
  Serial.begin(9600);

  vw_set_ptt_inverted(true); // Required for DR3100
  vw_set_rx_pin(8);
  vw_setup(1000); // Bits per sec
  vw_rx_start(); // Start the receiver PLL running

  // give the Ethernet shield a second to initialize:
  delay(1000);
  Serial.println("connecting...");

  telnet_connect();
}

void loop() {
	uint8_t buf[VW_MAX_MESSAGE_LEN];
	uint8_t buflen = VW_MAX_MESSAGE_LEN;  
	// if there are incoming bytes available 
	// from the server, read them and print them:
	if (client.available()) {
		char c = client.read();
		Serial.print(c); 
	}

	if (vw_get_message(buf, &buflen)) {
	  if(buflen == 1) { // if just one character per time
		if(buf[0]==13){
		  Serial.println("");
		  client.println(""); }
		else {
		  Serial.print(char(buf[0]));
		  client.print(char(buf[0]));
		}
	  }
	  else
		for(int n=0;n<buflen;n++) {
		  if(buf[n]==13) {
			Serial.println(""); // newline
			client.println(""); // newline
		  }
		Serial.print(char(buf[n]));
		client.print(char(buf[n]));
	  }
	  Serial.println(""); // insert newline at end of buffer
	  client.println(""); // insert newline at end of buffer
	}

  // as long as there are bytes in the serial queue,
  // read them and send them out the socket if it's open:
	while (Serial.available() > 0) {
		char inChar = Serial.read();
		
		if (client.connected()) {
			client.print(inChar); 
		}
		
	}

  // if the server's disconnected, stop the client:
  if (!client.connected()) {
    Serial.println();
    Serial.println("disconnecting.");
    client.stop();
    delay(15000); // Wait 15s.
    telnet_connect();  // Try to establish the connection back.
  }
}
