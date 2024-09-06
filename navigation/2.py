import cv2
import mediapipe as mp
import pyautogui

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)

left_hand_open = False
left_hand_closed = False

click_counter = 0

x1_ratio, y1_ratio = 2560 / 640, 1440 / 480

while True:
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Rileva le mani nell'immagine
    results = hands.process(image_rgb)
    h, w, _ = image.shape  # Altezza e larghezza dell'immagine

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Determina se è la mano destra o sinistra
            label = handedness.classification[0].label

            # Coordinate della punta dell'indice
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x = int(index_finger_tip.x * w)
            y = int(index_finger_tip.y * h)

            if label == 'Right':
                # pyautogui.moveTo(x, y)
                pyautogui.moveTo(int(x * x1_ratio), int(y * y1_ratio))
            elif label == 'Left':
                # Calcola la distanza tra la punta del pollice e la punta del mignolo per determinare apertura/chiusura
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
                distance = ((thumb_tip.x - pinky_tip.x) ** 2 + (thumb_tip.y - pinky_tip.y) ** 2) ** 0.5
                
                print("Distance", distance)

                if distance < 0.1:
                    left_hand_closed = True
                else:
                    if left_hand_closed:
                        # pyautogui.click()
                        click_counter += 1
                        print(click_counter, "Click")
                        left_hand_closed = False

            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Tracking", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
