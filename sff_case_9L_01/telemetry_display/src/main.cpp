#include <Arduino.h>

#define LCD_BL 22

void setup() {
  Serial.begin(115200);
  
  // 3000ms delay ensures USB CDC enumeration completes before serial output
  delay(3000); 
  Serial.println("--- CORRECT PIN BACKLIGHT TEST ---");

  pinMode(LCD_BL, OUTPUT);
}

void loop() {
  Serial.println("Backlight ON (GPIO 22)");
  digitalWrite(LCD_BL, HIGH);
  delay(2000);
  
  Serial.println("Backlight OFF (GPIO 22)");
  digitalWrite(LCD_BL, LOW);
  delay(2000);
}