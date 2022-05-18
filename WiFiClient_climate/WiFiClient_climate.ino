#include <ESP8266WiFi.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(D3, D4); // D3 - к TX сенсора, D4 - к RX

#define STASSID //имя вайфай сети
#define STAPSK //пароль вайфай сети
#define HOST_IP //адрес сервера
#define HOST_PORT //порт сервера
#define PERIOD_SEND 180 //600 // отправляем данные раз в 3 или 10 минут
#define API_DB //проверочный апи для базы
#define API_POL //проверочный апи для опроса датчика


const char* ssid = STASSID;
const char* password = STAPSK;
const char* host = HOST_IP;
const int port = HOST_PORT;
const String apiDB = API_DB;
const String api_polling = API_POL;

byte cmd[9] = {0xFF,0x01,0x86,0x00,0x00,0x00,0x00,0x00,0x79}; 
unsigned char response[9];


String msg = "";
String msg2 = "";
bool get_answer;
uint32_t curentTime = 0; 
double curentTime_mod = 0;
double curentTime_mod_prov = 0;
double curentTime_co2 = 0;
double curentTime_co2_get_prov = 0;
int mean_value[3];


void setup() {
  
  Serial.begin(115200);
  delay(60000); // задержка для прогрева датчика, нужно около 2 минут = 120000
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
  int periodCo2 = round(PERIOD_SEND/3);
  curentTime_co2 = curentTime / periodCo2;

  //========= раз в несколькок секунд (PERIOD_SEND) соединяемся с сервером и отправляем показания
  
  if ( (curentTime % PERIOD_SEND == 0) & (curentTime_mod != curentTime_mod_prov) ) {
    curentTime_mod_prov = curentTime_mod;
   
    connection();
    
  }
  
  //========= раз в несколькок секунд (periodCo2) берем показания и записываем их в массив
  
  if ( (curentTime % periodCo2 == 0) & (curentTime_co2 != curentTime_co2_get_prov) ) {
    curentTime_co2_get_prov = curentTime_co2;

    update_co2();
    
    
  }  
}


void update_co2(){
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


void connection(){
    
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
    Serial.println("Server connected. Begin transfer");
    }
    
  data_sharing(client);

  // Close the connection
  Serial.println();
  Serial.println("Closing connection");
  client.stop();
  
  
}


void data_sharing(WiFiClient client){
  
  
  msg = "";
  while (client.available()) {
    char ch = static_cast<char>(client.read());
    msg = msg + String(ch);
    }
  if (msg.startsWith("connected")) {
    msg.remove(0, 10);
       
    if (msg == "0"){   // только отправить данные в БД
      
        int co2_value = meanSensorValue();
        get_answer = true;
        
        unsigned long timeoutAnswer = millis();
        client.print(apiDB+";"+String(co2_value));
        delay(500);
        
        while (get_answer){
          if (millis()-timeoutAnswer < 3000){
            msg2 = "";
            while (client.available()) {
              char ch = static_cast<char>(client.read());
              msg2 = msg2 + String(ch);
              }
            Serial.println("msg2 = " + msg2);
            if (msg2 == "getted"){
              get_answer = false;
              Serial.println("=== Data send - ok"); 
              }
            else {
              client.print(apiDB+";"+String(co2_value));
              delay(500);
              }
            }
          }
        }
    else{ // отправляем данные в течении 3 минут, с интервалом заданным в msg
        unsigned long cur_time = millis();
        int time_ = msg.toInt()*1000;
        bool next_pol = true;
        while ((millis()-cur_time < 180000)&&(next_pol)){
          int co2_value = readSensor();
          get_answer = true;
          unsigned long timeoutAnswer = millis();
          client.print(api_polling+";"+String(co2_value));
          delay(500);
          
          while (get_answer){
            if (millis()-timeoutAnswer < 3000){
              msg2 = "";
              while (client.available()) {
                char ch = static_cast<char>(client.read());
                msg2 = msg2 + String(ch);
                }
              Serial.println("msg2 = " + msg2);
              if (msg2.startsWith("getted")){
                get_answer = false;
                Serial.println("=== Data send - ok"); 
                }
              else if (msg2.startsWith("stop")){
                next_pol = false;
                get_answer = false;
                }
              else {
                client.print(api_polling+";"+String(co2_value));
                delay(500);
                }
              }
            }
          delay(time_);
          }
        client.print("disconnect");
        delay(300);
        }
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
