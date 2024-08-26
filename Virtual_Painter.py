import cv2
import numpy as np
import os
from Hand_Tracking_Module import HandDetectorMP

folder_path = "Interface_Pics"
img_list = os.listdir(folder_path)

overlay_list = []

pressed_keys = []

for file in img_list:
    img = cv2.imread(f'{folder_path}/{file}')
    img = cv2.resize(img, (1280, 125))
    overlay_list.append(img)

header = overlay_list[2]

draw_color = (0, 0, 0)

xp, yp = 0, 0

brush_thickness = 15

img_canvas = np.zeros((720, 1280, 3), np.uint8)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetectorMP(detection_con=0.85)

while True:
    success, img = cap.read()

    img = cv2.flip(img, 1)

    img = detector.find_hands(img)

    lm_list = detector.find_position(img, draw=False)

    if len(lm_list) != 0:
        x1, y1 = lm_list[8][1:]
        x2, y2 = lm_list[12][1:]

        fingers = detector.fingers_up()
        total_fingers = fingers.count(1)

        if fingers[1] and fingers[2]:
            xp, yp = 0, 0
            cv2.rectangle(img, (x1, y1 - 15), (x2, y2 + 25), draw_color, cv2.FILLED)

            if y1 < 125:
                if 250 < x1 < 350:
                    header = overlay_list[4]
                    draw_color = (0, 0, 255)
                elif 400 < x1 < 550:
                    header = overlay_list[0]
                    draw_color = (255, 0, 0)
                elif 650 < x1 < 850:
                    header = overlay_list[3]
                    draw_color = (0, 255, 0)
                elif 900 < x1 < 1000:
                    header = overlay_list[1]
                    draw_color = (0, 0, 0)

        elif fingers[1]:
            cv2.circle(img, (x1, y1), 15, draw_color, cv2.FILLED)

            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            cv2.line(img, (xp, yp), (x1, y1), draw_color, brush_thickness)
            cv2.line(img_canvas, (xp, yp), (x1, y1), draw_color, brush_thickness)

            xp, yp = x1, y1

    img_gray = cv2.cvtColor(img_canvas, cv2.COLOR_BGR2GRAY)
    _, img_inv = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
    img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, img_inv)
    img = cv2.bitwise_or(img, img_canvas)

    img[0:125, 0:1280] = header

    cv2.imshow("Canvas", img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        img_canvas = np.zeros((720, 1280, 3), np.uint8)
    elif key == ord('+'):
        brush_thickness += 1
    elif key == ord('-'):
        brush_thickness = max(1, brush_thickness - 1)
    elif 48 <= key <= 57:
        pressed_keys.append(key - 48)

        if len(pressed_keys) == 9:
            blue = int(''.join(map(str, pressed_keys[:3])))
            green = int(''.join(map(str, pressed_keys[4:7])))
            red = int(''.join(map(str, pressed_keys[7:10])))

            draw_color = (blue, green, red)

            print(pressed_keys)

            pressed_keys = []

cv2.destroyAllWindows()
cap.release()
