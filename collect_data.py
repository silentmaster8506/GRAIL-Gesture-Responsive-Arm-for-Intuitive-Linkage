# collect_data.py
import cv2
import mediapipe as mp
import csv
import os
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

GESTURES = {
    '0': 'open_palm',
    '1': 'fist',
    '2': 'point',
    '3': 'thumbs_up',
    '4': 'three_fingers',
    '5': 'pinch'
}

SAMPLES_PER_CLASS = 200
os.makedirs('dataset', exist_ok=True)
CSV_FILE = 'dataset/landmarks.csv'

# Write header if file doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        # 21 landmarks x 3 values (x, y, z) + label = 64 columns
        header = []
        for i in range(21):
            header += [f'x{i}', f'y{i}', f'z{i}']
        header.append('label')
        writer.writerow(header)

current_label = None
count = 0
collecting = False

print("Press 0-5 to start collecting for that gesture.")
print("Press Q to quit.")

while True:
    ret, img = cap.read()
    if not ret:
        continue

    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            if collecting and current_label is not None and count < SAMPLES_PER_CLASS:
                row = []
                for lm in handLms.landmark:
                    row += [lm.x, lm.y, lm.z]
                row.append(current_label)

                with open(CSV_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

                count += 1

                if count >= SAMPLES_PER_CLASS:
                    print(f"Done collecting {SAMPLES_PER_CLASS} samples for gesture {current_label} ({GESTURES[str(current_label)]})")
                    collecting = False
                    count = 0

    # UI
    status = f"Collecting: {GESTURES.get(str(current_label), '-')}  [{count}/{SAMPLES_PER_CLASS}]" if collecting else "Press 0-5 to collect | Q to quit"
    cv2.putText(img, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Data Collection", img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif chr(key) in GESTURES and not collecting:
        current_label = int(chr(key))
        collecting = True
        count = 0
        print(f"Started collecting for gesture {current_label}: {GESTURES[str(current_label)]}")

cap.release()
cv2.destroyAllWindows()
print("Data collection done. Check dataset/landmarks.csv")