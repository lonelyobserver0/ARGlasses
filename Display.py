from threading import Thread
from queue import Queue
from Hand_Tracking_Module import main as hand_tracking
import pyautogui
# import mouse
# from time import sleep
# import numpy as np

pyautogui.FAILSAFE = False
mov_flag = False
i = 0
x1_0, x1_1, x1_2, x1_3, x1_4, x1_5, x1_6, x1_7, x1_8, x1_9, x1_10 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
y1_0, y1_1, y1_2, y1_3, y1_4, y1_5, y1_6, y1_7, y1_8, y1_9, y1_10 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
sensibility = 100


def read_csv(csv_file):
    data = []
    with open(csv_file, 'r') as f:
        # create a list of rows in the CSV file
        rows = f.readlines()
        # strip white-space and newlines
        rows = list(map(lambda x: x.strip(), rows))

        for row in rows:
            row = row.split(',')
            data.append(row)

    return data


def hand_detector(out_q):
    hand_tracking(out_q)


def coordinates_average(data):
    global i, x1_0, x1_1, x1_2, x1_3, x1_4, x1_5, x1_6, x1_7, x1_8, x1_9, x1_10, y1_0, y1_1, y1_2, y1_3, y1_4, y1_5,\
        y1_6, y1_7, y1_8, y1_9, y1_10

    if i == 0:
        x1_0 = data[0][0]
        y1_0 = data[0][1]
    elif i == 1:
        x1_1 = data[0][0]
        y1_1 = data[0][1]
    elif i == 2:
        x1_2 = data[0][0]
        y1_2 = data[0][1]
    elif i == 3:
        x1_3 = data[0][0]
        y1_3 = data[0][1]
    elif i == 4:
        x1_4 = data[0][0]
        y1_4 = data[0][1]
    elif i == 5:
        x1_5 = data[0][0]
        y1_5 = data[0][1]
    elif i == 6:
        x1_6 = data[0][0]
        y1_6 = data[0][1]
    elif i == 7:
        x1_7 = data[0][0]
        y1_7 = data[0][1]
    elif i == 8:
        x1_8 = data[0][0]
        y1_8 = data[0][1]
    elif i == 9:
        x1_9 = data[0][0]
        y1_9 = data[0][1]
    elif i == 10:
        x1_10 = data[0][0]
        y1_10 = data[0][1]
        i = 0

    i = i + 1

    distance = ((x1_1 - x1_0)**2 + (y1_1 - y1_0)**2)**0.5
    global mov_flag

    if distance >= sensibility:
        mov_flag = True
        print("TRUE")
    else:
        mov_flag = False
        print("FALSE")

    x1_average = int(((x1_0 + x1_1 + x1_2 + x1_3 + x1_4 + x1_5 + x1_6 + x1_7 + x1_8 + x1_9 + x1_10) / 11))
    y1_average = int(((y1_0 + y1_1 + y1_2 + y1_3 + y1_4 + y1_5 + y1_6 + y1_7 + y1_8 + y1_9 + y1_10) / 11))

    return x1_average, y1_average


def cursor_handler(x1, y1, finger_1):
    # 2560 : 640 = 1440 : 480
    x_ratio = 2560 / 640
    y_ratio = 1440 / 480
    # x_real, y_real = (2560 - x1), (1440 - y1)
    # x_real, y_real = x_real * x_ratio, y_real * y_ratio
    x_real, y_real = (2560 - (x1 * x_ratio)), (1440 - (y1 * y_ratio))

    if x_real < 0:
        x_real = -x_real
    if y_real < 0:
        y_real = -y_real

    print("Display coordinates:", x_real, y_real)

    global mov_flag
    if finger_1 == 1 and mov_flag is True:
        pyautogui.moveTo(x_real, y_real, 0.1)


def cursor(in_q):

    while True:
        data = in_q.get()

        finger_0, finger_1, finger_2, finger_3, finger_4 = (data[1][0], data[1][1], data[1][2], data[1][3], data[1][4])

        x1, y1 = coordinates_average(data)

        print("#--------------------------------------------#")
        print("Raw coordinates:", data[0][0], data[0][1])

        cursor_handler(x1, y1, finger_1)


def main():
    q = Queue()

    t1 = Thread(target=hand_detector, args=(q, ), daemon=True)
    t2 = Thread(target=cursor, args=(q, ), daemon=True)

    t1.start()
    t2.start()


if __name__ == "__main__":
    main()
