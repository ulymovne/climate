#include <ESP8266WiFi.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(D3, D4); // D3 - к TX сенсора, D4 - к RX

#ifndef STASSID
#define STASSID //тут ssid вайфая
#define STAPSK  //пароль вайфая
#define PERIOD_SEND 600 //600 // отправляем данные раз в 10 минут
#define PERIOD_CO2 180 //180 // опрос датчика раз в 3 минут
#define API_DB //проверочный апи для базы
#endif

byte cmd[9] = {0xFF,0x01,0x86,0x00,0x00,0x00,0x00,0x00,0x79}; 
unsigned char response[9];

const char* ssid     = STASSID;
const char* password = STAPSK;
String msg = "";
String msg2 = "";
bool prov;
uint32_t curentTime = 0; 
double curentTime_mod = 0;
double curentTime_mod_prov = 0;

double curentTime_co2 = 0;
double curentTime_co2_prov = 0;
int mean_value[3];


const char* host = // адрес сервера
const uint16_t port = // порт сервера

void setup() {
  Serial.begin(115200);
  delay(120000); // задержка для прогрева датчика, нужно 2 минуты = 120000
  mySerial.begin(9600);
  
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address:  ");
  Serial.println(WiFi.localIP());

  int first_value_co2 = readSensor();
  mean_value[0] = first_value_co2;
  mean_value[1] = first_value_co2;
  mean_value[2] = first_value_co2;
}

void loop() {
  curentTime = round(millis()/1000);
  curentTime_mod = curentTime / PERIOD_SEND;
  curentTime_co2 = curentTime / PERIOD_CO2;
  
  if ( (curentTime % PERIOD_SEND == 0) & (curentTime_mod != curentTime_mod_prov) ) {
    curentTime_mod_prov = curentTime_mod;
    Serial.println("Zahod time:  " + String(curentTime));
    
    int co2_value = meanSensorValue();
    
    Serial.print("connecting to ");
    Serial.print(host);
    Serial.print(':');
    Serial.println(port);
  
    // Use WiFiClient class to create TCP connections
    WiFiClient client;
    if (!client.connect(host, port)) {
      Serial.println("connection failed");
      delay(5000);
      return;
    }
  
    // This will send a string to the server
      
    // wait for data to be available
    unsigned long timeout = millis();
    while (client.available() == 0) {
      if (millis() - timeout > 5000) {
        Serial.println("=== Client Timeout !");
        client.stop();
        delay(10000);
        return;
      }
    }
  
    if (client.connected()) {
      Serial.println("=== Connected - OK");
    }
      
    msg = "";
    
    
    while (client.available()) {
      char ch = static_cast<char>(client.read());
      msg = msg + String(ch);
          }
    if (msg == "connected_ok") {
      prov = true;
      unsigned long timeoutAnswer = millis();
      
      client.print(API_DB + ";" + String(co2_value));
      delay(300);
      
      while (prov){
        if (millis()-timeoutAnswer < 3000){
          msg2 = "";
          while (client.available()) {
            char ch = static_cast<char>(client.read());
            msg2 = msg2 + String(ch);
            }
          Serial.println("msg2 = " + msg2);
          if (msg2 == "getted"){
            prov = false;
            Serial.println("=== Data send - ok"); 
        
          }
          else {
            client.print(API_DB + ";" + String(co2_value));
            delay(300);
          }
          
        }
        
      }
     
    }
      
  
    // Close the connection
    Serial.println();
    Serial.println("Closing connection");
    client.stop();
  }
  //раз в несколькок секунд=PERIOD_CO2 берем показания и записываем их в массив
  if ( (curentTime % PERIOD_CO2 == 0) & (curentTime_co2 != curentTime_co2_prov) ) {
    curentTime_co2_prov = curentTime_co2;
    //Serial.println("Pokazania datchika UP:  " + String(curentTime));
    int co2 = readSensor();
    if (co2 == 0){
      delay(2000);
      co2 = readSensor();
    }
    if (co2 == 0){
      co2 = meanSensorValue();
    }
    mean_value[0] = mean_value[1];
    mean_value[1] = mean_value[2];
    mean_value[2] = co2;
    
    //Serial.println(mean_value[2]);
  }  
}


int readSensor() {
    mySerial.write(cmd, 9);
    memset(response, 0, 9);
    delay(10);
    mySerial.readBytes(response, 9);
    int i;
    int ppm = 0;
    byte crc = 0;
    for (i = 1; i < 8; i++) crc+=response[i];
    crc = 255 - crc;
    crc++;
  
    if ( !(response[0] == 0xFF && response[1] == 0x86 && response[8] == crc) ) 
    {
      Serial.println("CRC error: " + String(crc) + " / "+ String(response[8]));
      while (mySerial.available()) {
        mySerial.read();
      }
    }
    else 
    {
      unsigned int responseHigh = (unsigned int) response[2];
      unsigned int responseLow = (unsigned int) response[3];
      ppm = (256*responseHigh) + responseLow;
      Serial.println("CO2 value:  " + String(ppm));
    }
   return ppm;
}

int meanSensorValue() {
  int mean_ = round((mean_value[0] + mean_value[1] + mean_value[2])/3);
  return mean_;
}
