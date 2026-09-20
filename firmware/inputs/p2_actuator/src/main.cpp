#include <Arduino.h>

#define TRIGGER_PIN PA0
unsigned long lastPress = 0;

void setup() {
    Serial.begin(115200);
    pinMode(TRIGGER_PIN, INPUT_PULLDOWN);
}

void loop() {
    if(digitalRead(TRIGGER_PIN) == HIGH) {
        if(millis() - lastPress < 50) {
            Serial.println("ACTUATOR: BOUNCE IGN");
        } else {
            Serial.println("ACTUATOR: ON");
            lastPress = millis();
        }
    }
    delay(10);
}
