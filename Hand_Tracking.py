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

        self.results = 0
        self.lm_list = []

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:

            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms,
                                                self.mp_hands.HAND_CONNECTIONS)

        return img

    def find_position(self, img, hand_no=0, draw=True):
        self.lm_list = []

        if self.results.multi_hand_landmarks:
            selected_hand = self.results.multi_hand_landmarks[hand_no]
            for l_id, lm in enumerate(selected_hand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([l_id, cx, cy])

                if draw:
                    cv2.circle(img, (cx, cy), 10, (200, 100, 200), cv2.FILLED)

        return self.lm_list

    def fingers_up(self):
        fingers = []

        # Thumb
        if self.lm_list[self.tip_ids[0]][1] > self.lm_list[self.tip_ids[1]][1]:  # right hand
            if self.lm_list[self.tip_ids[0]][1] > self.lm_list[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif self.lm_list[self.tip_ids[0]][1] < self.lm_list[self.tip_ids[1]][1]:
            if self.lm_list[self.tip_ids[0]][1] < self.lm_list[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        # ------------------- Resolving 4 elements array instead of 5 ----------------------
        else:
            fingers.append("BLANK")
        # -----------------------------------------

        # 4 Fingers
        for t_id in range(1, 5):
            if self.lm_list[self.tip_ids[t_id]][2] < self.lm_list[self.tip_ids[t_id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers


draw_color = (0, 255, 0)


def hand_tracking():

    p_time, fps = 0, 0

    x1_ratio, y1_ratio = 2560 / 640, 1440 / 480
    x1_offset, y1_offset = 40, 0

    cap = cv2.VideoCapture(0)
    detector = HandDetectorMP()

    counter, list_x, list_y, x1_average, y1_average = 0, [], [], 0, 0

    list_trigger = []

    while True:
        success, img = cap.read()
        img = detector.find_hands(img, draw=False)
        lm_list = detector.find_position(img, draw=False)

        if len(lm_list) != 0:

            x1, y1 = lm_list[8][1:]
            # x2, y2 = lm_list[12][1:]

            fingers = detector.fingers_up()
            total_fingers = fingers.count(1)

            c_time = time.time()
            fps = 1 / (c_time - p_time)
            p_time = c_time

            # <editor-fold desc="Coordinates elaboration">

            x1_real, y1_real = int((2560 - (x1 * x1_ratio)) - x1_offset), int((y1 * y1_ratio) - y1_offset)
            # """""
            # list_x.append(x1_real)
            # list_y.append(y1_real)
            list_trigger.append([x1_real, y1_real])
            counter += 1

            """""
            if counter % 2 == 0:
                x1_average = int(sum(list_x) / len(list_x))  # ((list_x[0] + list_x[1]) / 2)
                y1_average = int(sum(list_y) / len(list_y))  # ((list_y[0] + list_y[1]) / 2)
                list_x.clear()
                list_y.clear()

                print("#---------------------#")
                print("REAL COORDINATES         ", x1_real, y1_real)
                print("AVERAGE REAL COORDINATES ", x1_average, y1_average)
            """""

            if fingers[1] == 1:

                cv2.circle(img, (x1, y1), 5, draw_color, 2)
                pyautogui.moveTo(x1_real, y1_real, 0.01)
                # print(x1_real, y1_real)

                if counter == 3:

                    if list_trigger[0][1] != list_trigger[1][1]:
                        print(list_trigger[0][1], list_trigger[1][1])

                        trigger = list_trigger[2][1] - list_trigger[0][1]

                        if trigger < 10 or trigger > -10:

                            # pyautogui.leftClick(list_trigger[0][0], list_trigger[0][1], 0.01)
                            # print(x1_real, y1_real)
                            print("TRIGGERED")

                    counter = 0
                    list_trigger.clear()

            # """""
            # </editor-fold>

            # <editor-fold desc="Cursor moving">
            """""
            if fingers[1] == 1:
                print("#---------------------#")
                print("REAL COORDINATES         ", x1_real, y1_real)
                print("AVERAGE REAL COORDINATES ", x1_average, y1_average)
                # pyautogui.moveTo(x1_real, y1_real, 0.01)
            """""
            # </editor-fold>

        """
        img_inv = cv2.flip(img, 1)
        cv2.putText(img_inv, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_COMPLEX, 3,
                    (0, 256, 0), 3)

        cv2.imshow("Image", img_inv)
        """

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return 0


def display_handler():
    pass


if __name__ == "__main__":
    hand_tracking()
    display_handler()
