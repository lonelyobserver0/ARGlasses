import cv2
import mediapipe as mp
import time
import pyautogui

from google.protobuf.json_format import MessageToDict

pyautogui.FAILSAFE = False

class HandDetectorMP:
    def __init__(self, mode=False, max_hands=2, model_complexity=1, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_con = detection_con
        self.track_con = track_con

        self.tip_ids = [4, 8, 12, 16, 20]
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(self.mode, self.max_hands, self.model_complexity, self.detection_con, self.track_con)
        self.mp_draw = mp.solutions.drawing_utils

        self.results = None
        self.lm_list = []
        self.handedness = []

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)

        return img

    def find_position(self, img, draw=True):
        self.lm_list = []
        self.handedness = []

        if self.results.multi_hand_landmarks:
            for hand_no, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
                lm_list_single = []
                for l_id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list_single.append([l_id, cx, cy])

                    if draw:
                        cv2.circle(img, (cx, cy), 10, (200, 100, 200), cv2.FILLED)

                self.lm_list.append(lm_list_single)
                # Determine hand type (left or right)
                hand_label = self.results.multi_handedness[hand_no].classification[0].label
                self.handedness.append(hand_label)

        return self.lm_list, self.handedness

    def fingers_up(self):
        fingers = []
        for hand_index, hand_landmarks in enumerate(self.lm_list):
            fingers_single = []

            # Thumb
            if self.handedness[hand_index] == 'Right':
                if hand_landmarks[self.tip_ids[0]][1] > hand_landmarks[self.tip_ids[0] - 1][1]:
                    fingers_single.append(1)
                else:
                    fingers_single.append(0)
            else:  # Left hand
                if hand_landmarks[self.tip_ids[0]][1] < hand_landmarks[self.tip_ids[0] - 1][1]:
                    fingers_single.append(1)
                else:
                    fingers_single.append(0)

            # 4 Fingers
            for t_id in range(1, 5):
                if hand_landmarks[self.tip_ids[t_id]][2] < hand_landmarks[self.tip_ids[t_id] - 2][2]:
                    fingers_single.append(1)
                else:
                    fingers_single.append(0)

            fingers.append(fingers_single)

        return fingers

draw_color = (0, 255, 0)

def hand_tracking():

    x1_ratio, y1_ratio = 2560 / 640, 1440 / 480
    x1_offset, y1_offset = 40, 0

    cap = cv2.VideoCapture(0)
    detector = HandDetectorMP()

    counter, list_x, list_y, x1_average, y1_average = 0, [], [], 0, 0
    list_trigger = []

    while True:
        success, img = cap.read()
        img = detector.find_hands(img, draw=False)
        lm_list, handedness = detector.find_position(img, draw=False)

        if len(lm_list) != 0:
            for hand_index, hand_landmarks in enumerate(lm_list):
                x0, y0 = hand_landmarks[4][1:]
                x1, y1 = hand_landmarks[8][1:]
                x2, y2 = hand_landmarks[12][1:]
                x3, y3 = hand_landmarks[16][1:]
                x4, y4 = hand_landmarks[20][1:]
                fingers = detector.fingers_up()[hand_index]
                print(hand_index)
                total_fingers = fingers.count(1)

                x1_real, y1_real = int((2560 - (x1 * x1_ratio)) - x1_offset), int((y1 * y1_ratio) - y1_offset)
                list_trigger.append([x1_real, y1_real])
                counter += 1

                cv2.circle(img, (x0, y0), 5, draw_color, 2)
                cv2.circle(img, (x1, y1), 5, draw_color, 2)
                cv2.circle(img, (x2, y2), 5, draw_color, 2)
                cv2.circle(img, (x3, y3), 5, draw_color, 2)
                cv2.circle(img, (x4, y4), 5, draw_color, 2)

                '''if fingers[1] == 1:
                    cv2.circle(img, (x1, y1), 5, draw_color, 2)
                    pyautogui.moveTo(x1_real, y1_real, 0.01)

                    if counter == 3:
                        if list_trigger[0][1] != list_trigger[1][1]:
                            trigger = list_trigger[2][1] - list_trigger[0][1]

                            if trigger < 10 or trigger > -10:
                                print("TRIGGERED")

                        counter = 0
                        list_trigger.clear()'''

        img_inv = cv2.flip(img, 1)
        cv2.imshow("Image", img_inv)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return 0

if __name__ == "__main__":
    hand_tracking()
