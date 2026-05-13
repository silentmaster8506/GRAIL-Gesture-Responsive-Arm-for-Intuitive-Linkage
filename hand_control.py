import cv2
import mediapipe as mp
import serial
import time

# --- SERIAL SETUP ---
SERIAL_PORT = 'COM14'
esp32 = serial.Serial(SERIAL_PORT, 9600)
time.sleep(2)

# --- HAND TRACKING ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

tipIds = [4, 8, 12, 16, 20]
last_sent = ""
last_send_time = 0
SEND_DELAY = 0.3  # seconds — creates the visible ~0.5–1s lag


def is_hand_flipped(lmList, handedness_label):
    """
    Detect if the back of the hand is facing the camera.
    Uses wrist (0) and MCP joints to compute palm normal direction.
    For a mirrored (flipped) image:
      - Right hand (label='Right') → back facing if wrist.x > middle_MCP.x
      - Left  hand (label='Left')  → back facing if wrist.x < middle_MCP.x
    A simpler cross-product approach works more reliably across both hands.
    """
    # Use index MCP (5), pinky MCP (17), and wrist (0)
    wrist     = lmList[0]
    index_mcp = lmList[5]
    pinky_mcp = lmList[17]

    # 2D cross product of (index_mcp - wrist) x (pinky_mcp - wrist)
    # Positive z → palm faces camera; Negative z → back faces camera
    ax = index_mcp[1] - wrist[1]
    ay = index_mcp[2] - wrist[2]
    bx = pinky_mcp[1] - wrist[1]
    by = pinky_mcp[2] - wrist[2]

    cross_z = ax * by - ay * bx

    # After cv2.flip(img, 1), palm-facing = cross_z < 0 for right hand
    # Flip logic per handedness for robustness
    if handedness_label == 'Right':
        return cross_z > 0   # back of hand facing camera
    else:
        return cross_z < 0


def thumb_touching_pinky_base(lmList):
    """
    Returns True when thumb tip (landmark 4) is close to
    the base of the little finger / pinky MCP (landmark 17).
    Distance threshold tuned for normalized-to-pixel coords.
    """
    thumb_tip  = lmList[4]
    pinky_base = lmList[17]

    dist = ((thumb_tip[1] - pinky_base[1]) ** 2 +
            (thumb_tip[2] - pinky_base[2]) ** 2) ** 0.5

    # Scale threshold relative to hand size (wrist→middle_MCP distance)
    wrist      = lmList[0]
    middle_mcp = lmList[9]
    hand_size  = ((wrist[1] - middle_mcp[1]) ** 2 +
                  (wrist[2] - middle_mcp[2]) ** 2) ** 0.5

    # Thumb tip is "touching" pinky base if within 30% of hand size
    return dist < hand_size * 0.30


while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    fingers = []
    debug_lines = []

    if results.multi_hand_landmarks and results.multi_handedness:
        for handLms, handInfo in zip(results.multi_hand_landmarks,
                                     results.multi_handedness):
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            handedness_label = handInfo.classification[0].label  # 'Left' or 'Right'

            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, _ = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])

            if not lmList:
                continue

            # ---------- FINGER STATE DETECTION ----------

            # Thumb: compare tip (4) x vs joint (3) x
            fingers.append(1 if lmList[4][1] > lmList[3][1] else 0)

            # Index, Middle, Ring, Pinky: tip y vs two-below-tip y
            for i in range(1, 5):
                fingers.append(
                    1 if lmList[tipIds[i]][2] < lmList[tipIds[i] - 2][2] else 0
                )

            # ---------- SERVO ANGLE MAPPING ----------
            # Polarity note:
            #   s1 Thumb base  : open=180, close=0   (normal)
            #   s2 Index       : open=180, close=0   (REVERSED per user spec — wait, see below)
            #   s3 Middle      : open=0,   close=180 (normal polarity reversed)
            #   s4 Ring+Pinky  : open=180, close=0   (REVERSED per user spec)
            #   s5 Thumb tip   : open=180, close=0   (normal) — only on thumb-to-pinky gesture
            #   s6 Wrist       : 180 when hand flipped, else 0
            #
            # User spec: "ring/pinky and index → close=0, open=180"
            #            "other servos → close=180, open=0"

            # s1 — Thumb base (close=180, open=0)
            thumb_tip_servo = 180 if fingers[0] else 0

            # s2 — Index (close=0, open=180)
            index_servo = 180 if fingers[1] else 0

            # s3 — Middle (close=180, open=0)
            middle_servo = 0 if fingers[2] else 180

            # s4 — Ring + Pinky (close=0, open=180)
            # Finger open if EITHER ring OR pinky is extended
            ring_pinky_open = bool(fingers[3] or fingers[4])
            ring_pinky = 180 if ring_pinky_open else 0

            # s5 — Thumb tip mini (close=180, open=0)
            # Moves ONLY when thumb tip touches pinky base
            if thumb_touching_pinky_base(lmList):
                thumb_base = 180  # rotated / activated
            else:
                thumb_base = 90    # resting

            # s6 — Wrist (180 when back of hand faces camera, else 0)
            flipped = is_hand_flipped(lmList, handedness_label)
            wrist = 180 if flipped else 0

            # ---------- BUILD & SEND DATA STRING ----------
            data = (f"{thumb_base},"
                    f"{index_servo},"
                    f"{middle_servo},"
                    f"{ring_pinky},"
                    f"{thumb_tip_servo},"
                    f"{wrist}")

            current_time = time.time()
            if data != last_sent and (current_time - last_send_time) >= SEND_DELAY:
                esp32.write((data + '\n').encode())
                last_sent = data
                last_send_time = current_time

            # ---------- ON-SCREEN DEBUG ----------
            debug_lines = [
                f"Fingers : {fingers}",
                f"ThumbBase: {thumb_base}  Index: {index_servo}",
                f"Middle  : {middle_servo}  R+P: {ring_pinky}",
                f"ThumbTip: {thumb_tip_servo}  Wrist: {wrist}",
                f"Flipped : {flipped}",
                f"Sent    : {data}",
            ]

    # Draw debug info
    for i, line in enumerate(debug_lines):
        cv2.putText(img, line, (10, 30 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)

    cv2.imshow("Hand Control", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
