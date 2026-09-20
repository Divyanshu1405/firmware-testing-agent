#include <Arduino.h>

#define ADC_PIN PA1
int readArray[5];

void setup() {
    Serial.begin(115200);
    for(int i = 0; i < 5; i++) readArray[i] = 0;
}

void loop() {
    int val = analogRead(ADC_PIN);
    if(val > 4000) {
        Serial.println("ADC: FILTER OUTLIER");
    } else {
        // shift and avg
        int sum = val;
        for(int i=4; i>0; i--) {
            readArray[i] = readArray[i-1];
            sum += readArray[i];
        }
        readArray[0] = val;
        int avg = sum / 5;
        if(avg < 3000) {
            Serial.println("ADC: AVG OK");
        }
    }
    delay(50);
}
