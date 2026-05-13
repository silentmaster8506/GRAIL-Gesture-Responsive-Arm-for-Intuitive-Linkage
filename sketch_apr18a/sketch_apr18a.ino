#include <ESP32Servo.h>

Servo s1, s2, s3, s4, s5, s6;

String input = "";

void setup() {
  Serial.begin(9600);

  s1.attach(13); // Thumb
  s2.attach(12); // Index
  s3.attach(14); // Middle
  s4.attach(27); // Ring + Pinky
  s5.attach(26); // Thumb tip mini
  s6.attach(25); // Wrist
}

void loop() {

  if (Serial.available()) {
    input = Serial.readStringUntil('\n');

    int values[6];
    int index = 0;

    // Split CSV string
    for (int i = 0; i < input.length(); i++) {
      if (input[i] == ',') {
        index++;
      } else {
        values[index] = values[index] * 10 + (input[i] - '0');
      }
    }

    // Safety check
    if (index == 5) {

      s1.write(values[0]); // Thumb
      s2.write(values[1]); // Index
      s3.write(values[2]); // Middle
      s4.write(values[3]); // Ring + Pinky
      s5.write(values[4]); // Thumb tip
      s6.write(values[5]); // Wrist
    }

    // Reset values array
    for (int i = 0; i < 6; i++) values[i] = 0;
  }
}