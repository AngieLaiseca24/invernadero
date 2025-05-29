#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>

// ################################
// ### CONFIGURACIÓN DE PINES ###
// ################################

// Sensor de humedad del suelo
const int sueloPin = 1;  // GPIO1 (ADC1_CH0)

// Sensor DHT22
#define DHTPIN 10        // GPIO10
#define DHTTYPE DHT22
DHT_Unified dht(DHTPIN, DHTTYPE);

// Sensores de nivel líquido (horizontal/vertical)
#define SENSOR_H_MAX 2   // GPIO2
#define SENSOR_H_MIN 3   // GPIO3
#define BOMBA_HORIZONTAL 4 // GPIO4
#define BTN_H_START 5    // GPIO5
#define SENSOR_V 14      // GPIO14
#define BOMBA_VERTICAL 12 // GPIO12
#define BTN_V_START 13   // GPIO13

// ################################
// ### CONFIGURACIÓN WIFI/MQTT ###
// ################################
const char* WIFI_SSID = "USCO_CENTRAL";
const char* WIFI_PASS = "";
const char* MQTT_SERVER = "192.168.204.153";
const int MQTT_PORT = 1883;
const char* TOPIC = "iot/sensores";

WiFiClient espClient;
PubSubClient client(espClient);

// ################################
// ### FUNCIONES DE CONFIGURACIÓN ###
// ################################
void setup_wifi() {
  delay(10);
  Serial.begin(115200);
  Serial.println("\nConectando a " + String(WIFI_SSID));
  
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi conectado\nIP: " + WiFi.localIP().toString());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando MQTT...");
    if (client.connect("ESP32_MultiSensor")) {
      Serial.println("conectado");
      client.subscribe("iot/comandos"); // Tópico para recibir comandos
    } else {
      Serial.print("fallo, rc=");
      Serial.print(client.state());
      Serial.println(" reintento en 5s");
      delay(5000);
    }
  }
}

void setup() {
  // Inicializar DHT22
  dht.begin();
  
  // Configurar pines de sensores de nivel
  pinMode(SENSOR_H_MAX, INPUT_PULLUP);
  pinMode(SENSOR_H_MIN, INPUT_PULLUP);
  pinMode(BOMBA_HORIZONTAL, OUTPUT);
  pinMode(BTN_H_START, INPUT_PULLUP);
  pinMode(SENSOR_V, INPUT_PULLUP);
  pinMode(BOMBA_VERTICAL, OUTPUT);
  pinMode(BTN_V_START, INPUT_PULLUP);
  
  // Inicializar bombas apagadas
  digitalWrite(BOMBA_HORIZONTAL, LOW);
  digitalWrite(BOMBA_VERTICAL, LOW);

  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
}

// ################################
// ### FUNCIONES DE LECTURA ###
// ################################
String leerHorizontal() {
  if (digitalRead(SENSOR_H_MAX) == LOW) return "MAXIMO";
  else if (digitalRead(SENSOR_H_MIN) == LOW) return "MINIMO";
  else return "CRITICO";
}

String leerVertical() {
  return (digitalRead(SENSOR_V) == LOW) ? "VACIO" : "LLENO";
}

void controlBombas() {
  // Control automático sistema horizontal
  String estadoH = leerHorizontal();
  if (estadoH == "CRITICO") digitalWrite(BOMBA_HORIZONTAL, HIGH);
  else if (estadoH == "MAXIMO") digitalWrite(BOMBA_HORIZONTAL, LOW);

  // Control automático sistema vertical
  String estadoV = leerVertical();
  if (estadoV == "VACIO") digitalWrite(BOMBA_VERTICAL, HIGH);
  else digitalWrite(BOMBA_VERTICAL, LOW);
}

// ################################
// ### CALLBACK MQTT (COMANDOS) ###
// ################################
void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)message[i];

  if (String(topic) == "iot/comandos") {
    if (msg == "H_ON") digitalWrite(BOMBA_HORIZONTAL, HIGH);
    else if (msg == "H_OFF") digitalWrite(BOMBA_HORIZONTAL, LOW);
    else if (msg == "V_ON") digitalWrite(BOMBA_VERTICAL, HIGH);
    else if (msg == "V_OFF") digitalWrite(BOMBA_VERTICAL, LOW);
  }
}

// ################################
// ### LOOP PRINCIPAL ###
// ################################
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // --- Lectura de sensores ---
  // 1. Humedad del suelo
  int sueloValue = analogRead(sueloPin);
  String sueloEstado = (sueloValue > 1488) ? "SECO" : "HUMEDO";
  String payloadSuelo = "{\"valor\":" + String(sueloValue) + ",\"estado\":\"" + sueloEstado + "\"}";

  // 2. DHT22 (temperatura y humedad ambiente)
  sensors_event_t temp_event, hum_event;
  dht.temperature().getEvent(&temp_event);
  dht.humidity().getEvent(&hum_event);
  float temperatura = temp_event.temperature;
  float humedad = hum_event.relative_humidity;
  String payloadAmbiente = "{\"temperatura\":" + String(temperatura, 1) + ",\"humedad\":" + String(humedad, 1) + "}";

  // 3. Sensores de nivel líquido
  String nivelH = leerHorizontal();
  String nivelV = leerVertical();
  String payloadNivel = "{\"horizontal\":\"" + nivelH + "\",\"vertical\":\"" + nivelV + "\"}";

  // --- Publicar en MQTT (Topics separados) ---
  client.publish("iot/suelo", payloadSuelo.c_str());
  client.publish("iot/ambiente", payloadAmbiente.c_str());
  client.publish("iot/nivel", payloadNivel.c_str());

  // --- Log en Serial Monitor ---
  Serial.println("📤 Enviados:");
  Serial.println("- Tópico 'iot/suelo': " + payloadSuelo);
  Serial.println("- Tópico 'iot/ambiente': " + payloadAmbiente);
  Serial.println("- Tópico 'iot/nivel': " + payloadNivel);

  // --- Control de bombas y botones  ---
  controlBombas();
  if (digitalRead(BTN_H_START) == LOW) {
    digitalWrite(BOMBA_HORIZONTAL, !digitalRead(BOMBA_HORIZONTAL));
    delay(300);
  }
  if (digitalRead(BTN_V_START) == LOW) {
    digitalWrite(BOMBA_VERTICAL, !digitalRead(BOMBA_VERTICAL));
    delay(300);
  }

  delay(5000); // Espera 5 segundos entre lecturas
}