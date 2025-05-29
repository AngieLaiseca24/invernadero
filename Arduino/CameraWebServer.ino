// MQTT_Camera_SingleChunk.ino

#include <WiFi.h>
#include "esp_camera.h"
#include "mbedtls/base64.h"

// Permitir mensajes hasta ~16 KB
#define MQTT_MAX_PACKET_SIZE         16384
#define PUBSUBCLIENT_MAX_PACKET_SIZE 16384
#include <PubSubClient.h>

// ————— Configuración Wi-Fi / MQTT —————
const char* WIFI_SSID     = "USCO_CENTRAL";
const char* WIFI_PASS     = "";  // tu clave
const char* MQTT_SERVER   = "192.168.204.153";
const int   MQTT_PORT     = 1883;
const char* COMMAND_TOPIC = "camara/comando";
const char* PHOTO_TOPIC   = "camara/foto";

// Pines AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WiFiClient    wifiClient;
PubSubClient  mqttClient(wifiClient);

// Buffer Base64 en PSRAM
static char *b64buf = nullptr;
static size_t b64buf_len = 0;

void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int len);
void takeAndSendPhoto();

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("=== MQTT_Camera_SingleChunk ===");

  // Conectar Wi-Fi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("✔ WiFi conectado: " + WiFi.localIP().toString());

  // Inicializar cámara en QVGA
  camera_config_t cfg;
  cfg.ledc_channel = LEDC_CHANNEL_0;
  cfg.ledc_timer   = LEDC_TIMER_0;
  cfg.pin_d0       = Y2_GPIO_NUM;
  cfg.pin_d1       = Y3_GPIO_NUM;
  cfg.pin_d2       = Y4_GPIO_NUM;
  cfg.pin_d3       = Y5_GPIO_NUM;
  cfg.pin_d4       = Y6_GPIO_NUM;
  cfg.pin_d5       = Y7_GPIO_NUM;
  cfg.pin_d6       = Y8_GPIO_NUM;
  cfg.pin_d7       = Y9_GPIO_NUM;
  cfg.pin_xclk     = XCLK_GPIO_NUM;
  cfg.pin_pclk     = PCLK_GPIO_NUM;
  cfg.pin_vsync    = VSYNC_GPIO_NUM;
  cfg.pin_href     = HREF_GPIO_NUM;
  cfg.pin_sscb_sda = SIOD_GPIO_NUM;
  cfg.pin_sscb_scl = SIOC_GPIO_NUM;
  cfg.pin_pwdn     = PWDN_GPIO_NUM;
  cfg.pin_reset    = RESET_GPIO_NUM;
  cfg.xclk_freq_hz = 20000000;
  cfg.pixel_format = PIXFORMAT_JPEG;
  cfg.frame_size   = FRAMESIZE_QVGA;
  cfg.jpeg_quality = 12;
  cfg.fb_location  = CAMERA_FB_IN_PSRAM;
  cfg.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  cfg.fb_count     = psramFound() ? 2 : 1;

  if (esp_camera_init(&cfg) != ESP_OK) {
    Serial.println("❌ Error al iniciar cámara");
    while (true) delay(1000);
  }
  Serial.println("✔ Cámara inicializada");

  // Pre-asignar buffer Base64 en PSRAM (por ejemplo 16 KB)
  b64buf_len = 16384;
  b64buf = (char*)ps_malloc(b64buf_len);
  if (!b64buf) {
    Serial.println("❌ No hay PSRAM para b64buf");
    while (true) delay(1000);
  }

  // Configurar MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  reconnectMQTT();
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("↻ Conectando a MQTT...");
    if (mqttClient.connect("esp32_cam_single")) {
      Serial.println("✔ Conectado");
      if (mqttClient.subscribe(COMMAND_TOPIC, 1)) {
        Serial.print("✔ Suscrito a: ");
        Serial.println(COMMAND_TOPIC);
      } else {
        Serial.println("❌ Falló suscripción");
      }
    } else {
      Serial.print(" fallo rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String cmd((char*)payload, len);
  Serial.println();
  Serial.print("← Recibido comando: ");
  Serial.println(cmd);
  if (cmd == "toma foto") {
    takeAndSendPhoto();
  }
}

void takeAndSendPhoto() {
  Serial.println("▶ Capturando foto…");
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Falló captura");
    return;
  }

  // Codificar JPEG a Base64
  size_t out_len = b64buf_len;
  if (mbedtls_base64_encode((unsigned char*)b64buf, b64buf_len, &out_len, fb->buf, fb->len) != 0) {
    Serial.println("❌ Error Base64");
    esp_camera_fb_return(fb);
    return;
  }
  esp_camera_fb_return(fb);

  Serial.printf("↑ Publicando %u bytes usando streaming…\n", (unsigned)out_len);
  // 1) Comenzar publicación en streaming (no copia internamente)
  if (mqttClient.beginPublish(PHOTO_TOPIC, out_len, false)) {
    // 2) Escribir directamente el buffer
    mqttClient.write((uint8_t*)b64buf, out_len);
    // 3) Finalizar publicación
    mqttClient.endPublish();
    Serial.println("✔ Publicación streaming OK");
  } else {
    Serial.println("❌ Falló beginPublish");
  }
}


void loop() {
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();
}
