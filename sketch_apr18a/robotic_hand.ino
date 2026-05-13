/*
  Robotic Hand – ESP32 Servo Controller
  ======================================
  Pin map (matches Python send order):
    s1  GPIO 13  – Thumb base          (close=180, open=0)
    s2  GPIO 12  – Index               (close=0,   open=180)
    s3  GPIO 14  – Middle              (close=180, open=0)
    s4  GPIO 27  – Ring + Pinky        (close=0,   open=180)
    s5  GPIO 26  – Thumb tip mini      (activated=180, rest=0)
    s6  GPIO 25  – Wrist               (flipped=180, normal=0)

  CSV format received over Serial: "v0,v1,v2,v3,v4,v5\n"
  All values 0–180 degrees.
*/

#include <ESP32Servo.h>

Servo s1, s2, s3, s4, s5, s6;

// Clamp helper to keep angles safe
int clamp(int val, int lo = 0, int hi = 180) {
  if (val < lo) return lo;
  if (val > hi) return hi;
  return val;
}

void setup() {
  Serial.begin(9600);

  // Allocate timers (ESP32Servo needs this)
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  s1.setPeriodHertz(50);
  s2.setPeriodHertz(50);
  s3.setPeriodHertz(50);
  s4.setPeriodHertz(50);
  s5.setPeriodHertz(50);
  s6.setPeriodHertz(50);

  s1.attach(13, 500, 2400);  // Thumb base
  s2.attach(12, 500, 2400);  // Index
  s3.attach(14, 500, 2400);  // Middle
  s4.attach(27, 500, 2400);  // Ring + Pinky
  s5.attach(26, 500, 2400);  // Thumb tip mini
  s6.attach(25, 500, 2400);  // Wrist

  // Park all servos at their "open / rest" position on boot
  s1.write(0);    // Thumb base open
  s2.write(180);  // Index open
  s3.write(0);    // Middle open
  s4.write(180);  // Ring+Pinky open
  s5.write(0);    // Thumb tip rest
  s6.write(0);    // Wrist normal
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();   // strip CR/LF/spaces

    // Parse CSV — expect exactly 6 comma-separated integers
    int values[6] = {0, 0, 0, 0, 0, 0};
    int idx = 0;
    bool negative = false;

    for (int i = 0; i < input.length() && idx < 6; i++) {
      char c = input[i];
      if (c == ',') {
        idx++;
        negative = false;
      } else if (c == '-') {
        negative = true;
      } else if (c >= '0' && c <= '9') {
        values[idx] = values[idx] * 10 + (c - '0');
      }
    }

    // Only act if we received all 6 values
    if (idx == 5) {
      s1.write(clamp(values[0]));  // Thumb base
      s2.write(clamp(values[1]));  // Index
      s3.write(clamp(values[2]));  // Middle
      s4.write(clamp(values[3]));  // Ring + Pinky
      s5.write(clamp(values[4]));  // Thumb tip mini
      s6.write(clamp(values[5]));  // Wrist
    }
  }
}
