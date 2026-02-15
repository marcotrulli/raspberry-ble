#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ---------- WIFI ----------
const char* ssid = "Savosa";
const char* password = "Jarnobarbaraenzomarcoveronica5";

// ---------- SERVER ----------
WebServer server(80);

// ---------- STATO ----------
camera_fb_t* last_fb = NULL;
bool cameraOccupata = false;
unsigned long ultimoScatto = 0;
const unsigned long INTERVALLO_MINIMO = 2000; 

// ---------- CONFIG CAMERA (AI-THINKER) ----------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void configuraSensore() {
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    // RUOTA 180°
    s->set_vflip(s, 1);   
    s->set_hmirror(s, 1); 
    s->set_brightness(s, 1);
  }
}

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Errore Camera!");
    while(true);
  }
  configuraSensore();
}

void scattaFoto() {
  if(cameraOccupata || (millis() - ultimoScatto < INTERVALLO_MINIMO)) return;
  cameraOccupata = true;

  if(last_fb) esp_camera_fb_return(last_fb);
  last_fb = esp_camera_fb_get();
  
  if(last_fb) ultimoScatto = millis();
  cameraOccupata = false;
}

void handleRoot(){
  String ts = String(millis());
  String html = "<html><body style='text-align:center; font-family:Arial;'>";
  html += "<h2>ESP32-CAM Live</h2>";
  if(last_fb) html += "<img src='/image?t=" + ts + "' width='640' style='border:3px solid #333;'>";
  else html += "<p>Nessuna foto. Attesa segnale dal Raspberry...</p>";
  html += "<br><br><a href='/capture' style='padding:10px; background:green; color:white; text-decoration:none;'>SCATTO MANUALE</a>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleImage(){
  if(!last_fb) { server.send(404, "text/plain", "No image"); return; }
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.setContentLength(last_fb->len);
  server.send(200, "image/jpeg", "");
  WiFiClient client = server.client();
  client.write(last_fb->buf, last_fb->len);
}

void handleCapture(){
  scattaFoto();
  delay(100);
  server.sendHeader("Location","/");
  server.send(303);
}

void setup() {
  Serial.begin(115200);
  setupCamera();
  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED) delay(500);
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/image", handleImage);
  server.on("/capture", handleCapture);
  server.begin();
}

void loop(){ server.handleClient(); }
