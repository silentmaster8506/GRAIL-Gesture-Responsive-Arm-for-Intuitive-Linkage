# hand_control_with_model.py
import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import tensorflow as tf
import json

# ── Load model ──
model = tf.keras.models.load_model('gesture_model.h5')
with open('label_classes.json', 'r') as f:
    classes = json.load(f)

print(f"Loaded model. Classes: {classes}")

# ── Serial ──
SERIAL_PORT = 'COM14'
esp32 = serial.Serial(SERIAL_PORT, 9600)
time.sleep(2)

# ── MediaPipe ──
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
last_sent = ""
last_send_time = 0
SEND_DELAY = 0.3

# ── Gesture → servo angles mapping ──
# Customize these angles for your actual robot
GESTURE_SERVO_MAP = {
    'open_palm':     (0,   180, 0,   180, 180, 0),   # all open
    'fist':          (180, 0,   180, 0,   0,   0),   # all closed
    'point':         (180, 180, 180, 0,   0,   0),   # index up
    'thumbs_up':     (0,   0,   180, 0,   180, 0),   # thumb open
    'three_fingers': (180, 180, 0,   180, 0,   0),   # 3 fingers
    'pinch':         (90,  0,   180, 0,   90,  0),   # pinch
}

def normalize_landmarks(lms_array):
    lms = lms_array.reshape(21, 3)
    wrist = lms[0:1, :]
    lms = lms - wrist
    return lms.reshape(1, 63)

while True:
    ret, img = cap.read()
    if not ret:
        continue

    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    gesture_label = None

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            # Extract landmarks
            lms = []
            for lm in handLms.landmark:
                lms += [lm.x, lm.y, lm.z]
            lms = np.array(lms)

            # Normalize & predict
            lms_norm = normalize_landmarks(lms)
            pred = model.predict(lms_norm, verbose=0)
            confidence = np.max(pred)
            class_idx = np.argmax(pred)
            gesture_label = classes[class_idx]

            # Only act if confidence is high enough
            if confidence > 0.85 and gesture_label in GESTURE_SERVO_MAP:
                s1, s2, s3, s4, s5, s6 = GESTURE_SERVO_MAP[gesture_label]
                data = f"{s1},{s2},{s3},{s4},{s5},{s6}"

                current_time = time.time()
                if data != last_sent and (current_time - last_send_time) >= SEND_DELAY:
                    esp32.write((data + '\n').encode())
                    last_sent = data
                    last_send_time = current_time

            # Debug
            cv2.putText(img, f"Gesture : {gesture_label}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(img, f"Conf    : {confidence:.2f}", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(img, f"Sent    : {last_sent}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,200,255), 1)

    cv2.imshow("GRAIL - Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()