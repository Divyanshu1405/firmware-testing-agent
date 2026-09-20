#include <Arduino.h>

#define PWM_PIN PA2
int target = 0;

void setup() {
    Serial.begin(115200);
    pinMode(PWM_PIN, OUTPUT);
}

void loop() {
    if(Serial.available() > 0) {
        target = Serial.parseInt();
        if(target > 100) {
            target = 100;
            Serial.println("PWM: CLAMPED MAX");
        } else if (target < 0) {
            target = 0;
            Serial.println("PWM: CLAMPED MIN");
        } else {
            Serial.println("PWM: TARGET SET");
        }
        analogWrite(PWM_PIN, map(target, 0, 100, 0, 255));
    }
    delay(10);
}
