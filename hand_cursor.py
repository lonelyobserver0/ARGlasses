import cv2
import mediapipe as mp
import time
import math
from multiprocessing import Queue
from typing import Union # Importa Union

# Inizializza MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)
mp_drawing = mp.solutions.drawing_utils

def start_hand_tracking(output_queue: Queue, oled_width: int, oled_height: int) -> None:
    """
    Avvia il tracciamento della mano destra tramite MediaPipe e invia le coordinate
    del cursore e lo stato del click (pugno chiuso) a una coda.

    Args:
        output_queue (Queue): La coda multiprocessing per inviare i dati (x, y, click).
        oled_width (int): Larghezza del display OLED (es. 128 pixel).
        oled_height (int): Altezza del display OLED (es. 64 pixel).
    """
    print("Hand Tracker: Avvio del tracciamento della mano...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hand Tracker: Errore: Impossibile accedere alla telecamera.")
        output_queue.put((0, 0, False))
        return

    cam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Hand Tracker: Risoluzione telecamera: {cam_width}x{cam_height}")

    is_clicking = False
    last_click_time = time.time()
    click_debounce_time = 0.5

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Hand Tracker: Impossibile leggere il frame dalla telecamera. Uscita.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = hands.process(rgb_frame)

            cursor_x, cursor_y = oled_width // 2, oled_height // 2
            click_state = False

            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    if results.multi_handedness and hand_idx < len(results.multi_handedness):
                        handedness_label = results.multi_handedness[hand_idx].classification[0].label

                        if handedness_label == 'Right':
                            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                            
                            cam_x = int(index_finger_tip.x * cam_width)
                            cam_y = int(index_finger_tip.y * cam_height)

                            cursor_x = int(cam_x * (oled_width / cam_width))
                            cursor_y = int(cam_y * (oled_height / cam_height))
                            
                            cursor_x = max(0, min(oled_width - 1, cursor_x))
                            cursor_y = max(0, min(oled_height - 1, cursor_y))

                            flex_threshold = 0.05

                            is_index_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > 
                                               hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y + flex_threshold)
                            is_middle_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > 
                                                hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y + flex_threshold)
                            is_ring_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > 
                                              hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y + flex_threshold)
                            is_pinky_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y > 
                                               hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y + flex_threshold)
                            
                            current_fist_state = is_index_flexed and is_middle_flexed and is_ring_flexed and is_pinky_flexed
                            
                            if current_fist_state and not is_clicking and (time.time() - last_click_time > click_debounce_time):
                                click_state = True
                                is_clicking = True
                                last_click_time = time.time()
                                print("Hand Tracker: CLICK RILEVATO (Pugno Chiuso)")
                            elif not current_fist_state and is_clicking:
                                is_clicking = False

            output_queue.put((cursor_x, cursor_y, click_state))

            # cv2.imshow('Hand Tracking', frame) # Uncomment for visual debugging
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Hand Tracker: 'q' premuto. Uscita.")
                break

    except Exception as e:
        print(f"Hand Tracker: Errore critico nel loop: {e}")
    finally:
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Hand Tracker: Tracciamento mano terminato.")

if __name__ == '__main__':
    test_queue = Queue()
    start_hand_tracking(test_queue, oled_width=128, oled_height=64)

    try:
        while True:
            if not test_queue.empty():
                data = test_queue.get()
                print(f"Hand Tracker Test: Dati ricevuti da coda: {data}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Test di Hand Tracker interrotto.")
