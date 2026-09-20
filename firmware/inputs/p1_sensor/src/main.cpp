#include <Arduino.h>
#include <Wire.h>

void setup() {
    Serial.begin(115200);
    Wire.begin();
}

void loop() {
    Wire.requestFrom(0x40, 2);
    if(Wire.available() == 2) {
        int val = (Wire.read() << 8) | Wire.read();
        Serial.print("SENSOR: ");
        Serial.println(val);
        Serial.println("SENSOR: RECOVERY");
    } else {
        Serial.println("SENSOR: TIMEOUT");
    }
    delay(100);
}
