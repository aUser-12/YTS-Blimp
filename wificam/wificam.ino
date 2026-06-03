#include <WiFi.h>
#include <WiFiUdp.h>
#include "esp_camera.h"


#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 10
#define SIOD_GPIO_NUM 40
#define SIOC_GPIO_NUM 39
#define Y9_GPIO_NUM 48
#define Y8_GPIO_NUM 11
#define Y7_GPIO_NUM 12
#define Y6_GPIO_NUM 14
#define Y5_GPIO_NUM 16
#define Y4_GPIO_NUM 18
#define Y3_GPIO_NUM 17
#define Y2_GPIO_NUM 15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM  47
#define PCLK_GPIO_NUM  13

const char* ssid = "ESP32-CAM";
const char* pass = "12345678";

//ip to stream to
const char* CLIENT_IP = "192.168.4.2";
const uint16_t UDP_PORT = 5005;
const size_t MTU = 1400;   //udp gott be below 1500

WiFiUDP udp;

//4 bit bigendian
void sendU32(uint32_t v) {
  uint8_t buf[4] = {
    (uint8_t)(v >> 24),
    (uint8_t)(v >> 16),
    (uint8_t)(v >>  8),
    (uint8_t)(v      )
  };
  udp.beginPacket(CLIENT_IP, UDP_PORT);
  udp.write(buf, 4);
  udp.endPacket();
}

//each packet = 4 byte header and then mtu * n bites of  f r a m e
void streamFrame(camera_fb_t* fb) {
  sendU32((uint32_t)fb->len);           //tell receiver total byte count

  size_t offset = 0;
  while (offset < fb->len) {
    size_t chunk = min(MTU, fb->len - offset);
    udp.beginPacket(CLIENT_IP, UDP_PORT);
    udp.write(fb->buf + offset, chunk);
    udp.endPacket();
    offset += chunk;
    delayMicroseconds(200);             //pause dont lfood
  }
}

void startCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_1;
  config.ledc_timer = LEDC_TIMER_1;

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

  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size = FRAMESIZE_QQVGA;
  config.jpeg_quality = 30;
  config.fb_count = 1;
  config.fb_location  = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.xclk_freq_hz = 10000000;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }
  Serial.println("Camera OK");

  
  camera_fb_t* fb = esp_camera_fb_get();
  if (fb) { Serial.printf("Warmup OK: %d bytes\n", fb->len); esp_camera_fb_return(fb); }

  sensor_t* s = esp_camera_sensor_get();
  Serial.printf("Sensor PID: 0x%x\n", s->id.PID);
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);
  s->set_saturation(s, 0);
  s->set_gain_ctrl(s, 1);
  s->set_exposure_ctrl(s, 1);
  s->set_awb_gain(s, 1);
  s->set_aec2(s, 1);
  s->set_ae_level(s, 0);
  s->set_gainceiling(s, (gainceiling_t)4);
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, pass);
  Serial.printf("AP IP: %s\n", WiFi.softAPIP().toString().c_str());

  startCamera();
  delay(2000);

  udp.begin(UDP_PORT);
  Serial.printf("UDP streaming to %s:%d\n", CLIENT_IP, UDP_PORT);

  if (psramFound()) Serial.println("PSRAM found");
  else Serial.println("PSRAM not found");
}

void loop() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) { Serial.println("Capture failed"); delay(100); return; }

  Serial.printf("Sending frame: %d bytes\n", fb->len);
  streamFrame(fb);
  esp_camera_fb_return(fb);
}