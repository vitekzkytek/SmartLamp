#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

//const char* ssid = "Internet";
//const char* password = "MPF8GUV8CQ";
const char* ssid = "Zkytek IPhone";
const char* password = "c240jlcwodjo";

#define LEDka LED_BUILTIN
#define LEDka2 12

void setup () {
  pinMode(LEDka, OUTPUT);
  pinMode(LEDka2, OUTPUT);

  digitalWrite(LEDka, HIGH);
  digitalWrite(LEDka2, LOW);

  Serial.begin(115200);
  WiFi.begin(ssid, password);
   
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print("."); 
  }
}
 
void loop() { 
  if (WiFi.status() == WL_CONNECTED) { //Check WiFi connection status
    HTTPClient http;  //Declare an object of class HTTPClient
     
    http.begin("http://195.181.218.77:80/gimme_next/vitek");  //Specify request destination
    int httpCode = http.GET();  //Send the request
     
    if (httpCode > 0) { //Check the returning code
    const size_t capacity = JSON_ARRAY_SIZE(20) + JSON_OBJECT_SIZE(8) + 370;
    DynamicJsonDocument doc(capacity);
      
      String payload = http.getString();

      char buf[payload.length()+1];
      payload.toCharArray(buf,payload.length()+1);   //Get the request response payload
      DeserializationError error = deserializeJson(doc, buf);

      if (error) {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.c_str());
        return;
      }
      if (doc["result"] == "null") {
        Serial.println("nic");
      } else {
        if (doc["result"] == "success") {
          const char* morse = doc["morse_delimiters"].as<char*>();
          Serial.println(morse);
          int count = strlen(morse);

          for (int i = 0; i < count; i++) {
            char symbol = morse[i];
            if (symbol == '.') {
                MorseDot();  
            }
            if (symbol == '-') {
                MorseDash();
            }
            if (symbol == '_') {
                MorseSpace();
            }
          }
        }
      }
    }
  http.end();   //Close connection
  }
  delay(5000);    //Send a request every 5 seconds
}

const int dotLen = 500;
const int dashLen = 1000;
const int spaceLen = 2000;
const int betweenMorse = 300;

void MorseDot() {
  digitalWrite(LEDka, LOW);    // turn the LED on 
  digitalWrite(LEDka2, HIGH);    // turn the LED on 

  delay(dotLen);
  digitalWrite(LEDka, HIGH);// hold in this position
  digitalWrite(LEDka2, LOW);// hold in this position
  delay(betweenMorse);
}

void MorseDash() {
  digitalWrite(LEDka, LOW);    // turn the LED on 
  digitalWrite(LEDka2, HIGH);    // turn the LED on 
  delay(dashLen);
  digitalWrite(LEDka, HIGH);// hold in this position
  digitalWrite(LEDka2, LOW);// hold in this position
  delay(betweenMorse);
}

void MorseSpace() {
  delay(spaceLen);
}
