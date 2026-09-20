#include <Arduino.h>

void setup() {
    Serial.begin(115200);
}

void loop() {
    if(Serial.available() > 0) {
        String data = Serial.readStringUntil('\n');
        if(data == "READY_CMD") {
            Serial.println("UART: PARSED OK");
        } else {
            Serial.println("UART: DROP MALFORMED");
        }
    }
}
