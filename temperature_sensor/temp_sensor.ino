#include <Arduino.h>

// Web stuff
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <WiFiUDP.h>
#include <HTTPClient.h>
#include <NTPClient.h>

// Sensor stuff
#include "DHT.h"

//Display stuff
#include <TFT_eSPI.h>

#include "ssid_settings.h"

TFT_eSPI tft = TFT_eSPI();

#define DHTPIN 21
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

WiFiMulti wifiMulti;
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);
unsigned long lastTime = 0;

void setupWifi()
{
  wifiMulti.addAP(WIFI_SSID, WIFI_PW);
  while (wifiMulti.run() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
}

void setupScreen()
{
  tft.init();
  tft.setRotation(2);
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0, 4);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.println("Its Alive!");
  delay(5000);
  tft.fillScreen(TFT_BLACK);
}

void setupSensor()
{
  dht.begin();
}

void setupNTP()
{
  timeClient.begin();
}
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println(F("Test begin"));
  setupSensor();
  setupScreen();
  setupWifi();
  setupNTP();
}

void postData(float temperature, float humidity)
{
  HTTPClient http;
  http.useHTTP10(true);

  Serial.print("[HTTP] begin...\n");
  http.begin("http://mail.arlininger.com:5000/temperature"); //HTTP
  http.addHeader("Content-Type", "application/json");

//  Serial.print("[HTTP] GET...\n");
  // start connection and send HTTP header
  DynamicJsonDocument doc(2048);
  doc["timestamp"] = timeClient.getEpochTime();
  doc["Temperature"] = temperature;
  doc["Humidity"] = humidity;
  doc["sensor"] = "Sensor 0.1";
  String json;
  serializeJson(doc,json);
//  Serial.println(json);
  int httpCode = http.POST(json);

  // httpCode will be negative on error
  if(httpCode > 0) {
      // HTTP header has been send and Server response header has been handled
//      Serial.printf("[HTTP] GET... code: %d\n", httpCode);

      // file found at server
    if(httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
//      Serial.println(payload);
    } else if (httpCode == HTTP_CODE_CREATED) {
      String payload = http.getString();
//      Serial.println(payload);
//              deserializeJson(doc,http.getStream());
//              Serial.println(doc["records"][0]["Temperature"].as<float>());
//              Serial.println(doc["records"][0]["Humidity"].as<float>());
//              Serial.println("");
    } else {
      Serial.println(timeClient.getFormattedTime());
      Serial.print("Unrecognized return code...");
      Serial.println(httpCode);
    }
  } else {
      Serial.println(timeClient.getFormattedTime());
      Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
  
}

unsigned long getTime()
{
  timeClient.update();
  Serial.println(timeClient.getFormattedTime());
  return timeClient.getEpochTime();
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(2000);
  bool Farenheit = true;
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(Farenheit);

  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0, 4);

  tft.setTextColor(TFT_RED, TFT_BLACK);
  tft.println(temperature);
//  Serial.println(temperature);

  tft.setTextColor(TFT_BLUE, TFT_BLACK);
  tft.println(humidity);
//  Serial.println(humidity);

  if((wifiMulti.run() == WL_CONNECTED)) {
    unsigned long currentTime = getTime();
    if (currentTime > (lastTime + 60))
    {
      lastTime = currentTime;
      postData(temperature, humidity);
    }
  }

}
