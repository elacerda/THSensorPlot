// transmitter.pde
//
// Simple example of how to use VirtualWire to transmit messages.
// Implements a simplex (one-way) transmitter.
//
// See VirtualWire.h for detailed API docs
// Author: Mike McCauley (mikem@airspayce.com)
// Copyright (C) 2008 Mike McCauley
// $Id: transmitter.pde,v 1.3 2009/03/30 00:07:24 mikem Exp $
// TX data to Digital I/O pin 12.
// Sends DHT data.

#include <Wire.h>
#include <VirtualWire.h>
//#include <JeeLib.h>
//ISR(WDT_vect) { Sleepy::watchdogEvent(); }

#define DEBUG
#define RADIO_ID 10
#define DHT_PIN 9
#define DHT_TYPE 11
#define FOGGER_PIN 6
#define TX_PIN 12
#define TX_SPEED 1000

// Init DHT.
#if DHT_TYPE == 11
	#include <dht11.h> 
	dht11 DHT;
#elif DHT_TYPE == 22
	#include <dht.h>
	dht DHT;
#endif

// Init VWMsgBuf.
char VWMsgBuf[VW_MAX_MESSAGE_LEN];
// Init VWMsgStr.
String VWMsgStr;


// Init hello world count.
unsigned int cnt = 0;

//Rounds down (via intermediary integer conversion truncation)
String doubleToString(double input,int decimalPlaces){
	if(decimalPlaces!=0){
		String string = String((int)(input*pow(10,decimalPlaces)));
		if(abs(input)<1){
		if(input>0)
		string = "0"+string;
		else if(input<0)
		string = string.substring(0,1)+"0"+string.substring(1);
	}
		return string.substring(0,string.length()-decimalPlaces)+"."+string.substring(string.length()-decimalPlaces);
	}
	else {
		return String((int)input);
	}
}

// setup() runs once after reset.
void setup() {
  #ifdef DEBUG
    // Init serial for debugging.
    Serial.begin(9600);
  #endif
  // Init BPS.
  vw_setup(TX_SPEED);
  vw_set_ptt_inverted(true); //
  vw_set_tx_pin(TX_PIN);
  // Send setup() message.
  VWMsgStr = ":REMOTE1-  setup()!;";
  VWTX(VWMsgStr);
  #ifdef DEBUG
    Serial.println(VWMsgStr);
  #endif
  // FOGGER SETUP
  pinMode(FOGGER_PIN, OUTPUT);
  digitalWrite(FOGGER_PIN, HIGH);
}

// loop() runs continuously after setup().
void loop() {
  // Send hello world message.
//  VWMsgStr = "REMOTE1 - Hello World!  Count=" + String(cnt++);
//  VWTX(VWMsgStr);
//  #ifdef DEBUG
//    Serial.println(VWMsgStr);
//  #endif

  // Send DHT message.
  #if DHT_TYPE == 11
    Serial.println("Reading DHT11");
    int rc = DHT.read(DHT_PIN);
  #elif DHT_TYPE == 22
    Serial.println("Reading DHT22");
  	int rc = DHT.read22(DHT_PIN);
  #endif

  switch (rc) {
    case DHTLIB_OK:
      VWMsgStr = ":I" + String(RADIO_ID);
	  VWMsgStr += "H" + doubleToString(DHT.humidity,2);
	  VWMsgStr += "T" + doubleToString(DHT.temperature,2);
      VWMsgStr += ";";
      break;
    case DHTLIB_ERROR_CHECKSUM:
      VWMsgStr = ":REMOTE1- Checksum!;";
      break;
    case DHTLIB_ERROR_TIMEOUT:
      VWMsgStr = ":REMOTE1- Time Out!;";
      break;
    default:
      VWMsgStr = ":REMOTE1- Unknown!;";
      break;
  }

  VWTX(VWMsgStr);
  #ifdef DEBUG
    Serial.println(VWMsgStr);
  #endif
  
  delay(30000);
}

// Virtual Wire Transmit msgStr
void VWTX(String VWMsgStr) {
  VWMsgStr.toCharArray(VWMsgBuf, VW_MAX_MESSAGE_LEN);
  uint8_t VWMsgBufLen = strlen(VWMsgBuf);
  digitalWrite(13, true); // Flash a light to show transmitting
  vw_send((uint8_t *)VWMsgBuf, strlen(VWMsgBuf));
  vw_wait_tx(); // Wait until the whole message is gone
  digitalWrite(13, false);
  delay(1000);
//  Sleepy::loseSomeTime(30000);
}

/*
// Returns double fahrenheit from double celsius.
double fahrenheit(double celsius) {
  return 1.8 * celsius + 32;
}
*/

// Returns int fahrenheit from int celsius.
/*int fahrenheit(int celsius) {
  return (celsius * 18 + 5) / 10 + 32;
}*/

/*
// Returns double kelvin from double celsius.
double kelvin(double celsius) {
  return celsius + 273.15;
}

// dewPoint function NOAA
// reference (1) : http://wahiduddin.net/calc/density_algorithms.htm
// reference (2) : http://www.colorado.edu/geography/weather_station/Geog_site/about.htm
double dewPoint(double celsius, double humidity) {
  // (1) Saturation Vapor Pressure = ESGG(T)
  double RATIO = 373.15 / (273.15 + celsius);
  double RHS = -7.90298 * (RATIO - 1);
  RHS += 5.02808 * log10(RATIO);
  RHS += -1.3816e-7 * (pow(10, (11.344 * (1 - 1/RATIO ))) - 1) ;
  RHS += 8.1328e-3 * (pow(10, (-3.49149 * (RATIO - 1))) - 1) ;
  RHS += log10(1013.246);
  // factor -3 is to adjust units - Vapor Pressure SVP * humidity
  double VP = pow(10, RHS - 3) * humidity;
  // (2) DEWPOINT = F(Vapor Pressure)
  double T = log(VP/0.61078);   // temp var
  return (241.88 * T) / (17.558 - T);
}

// delta max = 0.6544 wrt dewPoint()
// 6.9 x faster than dewPoint()
// reference: http://en.wikipedia.org/wiki/Dew_point
double dewPointFast(double celsius, double humidity) {
  double a = 17.271;
  double b = 237.7;
  double temp = (a * celsius) / (b + celsius) + log(humidity*0.01);
  double Td = (b * temp) / (a - temp);
  return Td;
}
*/


