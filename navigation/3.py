import cv2
import dlib
import pyautogui
from scipy.spatial import distance

# Inizializza dlib per il rilevamento del volto e dei punti di riferimento facciali
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Funzione per calcolare la relazione occhio
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Funzione migliorata per trovare la posizione della pupilla
def find_pupil(eye, frame):
    eye_roi = frame[eye[1][1]:eye[4][1], eye[0][0]:eye[3][0]]
    eye_roi_gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
    eye_roi_gray = cv2.equalizeHist(eye_roi_gray)  # Migliora il contrasto

    # Usa una soglia adattiva per segmentare la pupilla
    eye_roi_blur = cv2.GaussianBlur(eye_roi_gray, (7, 7), 0)
    _, threshold = cv2.threshold(eye_roi_blur, 30, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Trova contorni
    contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Trova il contorno più grande, assumendo che sia la pupilla
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) > 5:
            (x, y), radius = cv2.minEnclosingCircle(largest_contour)
            if radius > 2:  # Controllo sul raggio per evitare falsi positivi
                pupil_center = (int(x), int(y))
                cv2.circle(eye_roi, pupil_center, int(radius), (0, 255, 0), 1)
                return pupil_center
    return None

# Definisce i punti chiave per gli occhi destro e sinistro
(left_eye_start, left_eye_end) = (42, 48)
(right_eye_start, right_eye_end) = (36, 42)

# Soglia per considerare un battito e contatore per doppio battito
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 3
counter = 0
blinks = 0

# Apri la webcam
cap = cv2.VideoCapture(0)

x_ratio, y_ratio = 2560 / 640, 1440 / 480
print(x_ratio, y_ratio)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    for rect in rects:
        shape = predictor(gray, rect)
        shape = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

        left_eye = shape[left_eye_start:left_eye_end]
        right_eye = shape[right_eye_start:right_eye_end]

        leftEAR = eye_aspect_ratio(left_eye)
        rightEAR = eye_aspect_ratio(right_eye)

        ear = (leftEAR + rightEAR) / 2.0

        # Controllo battito ciglia
        if ear < EYE_AR_THRESH:
            counter += 1
        else:
            if counter >= EYE_AR_CONSEC_FRAMES:
                blinks += 1
                if blinks == 3:
                    pyautogui.click()
                    blinks = 0
            counter = 0

        # Rilevamento delle pupille
        left_pupil = find_pupil(left_eye, frame)
        right_pupil = find_pupil(right_eye, frame)

        # Debug: Mostra le coordinate delle pupille
        if left_pupil and right_pupil:
            # print("Pupilla Sinistra:", left_pupil)
            # print("Pupilla Destra:", right_pupil)

            # Calcolo delle medie delle posizioni delle pupille per stimare la posizione dello sguardo
            avg_pupil_x = (left_pupil[0] + right_pupil[0]) / 2
            avg_pupil_y = (left_pupil[1] + right_pupil[1]) / 2

            # Mapparle alla risoluzione dello schermo
            screen_width, screen_height = pyautogui.size()
            screen_x = screen_width * (avg_pupil_x / frame.shape[1])
            screen_y = screen_height * (avg_pupil_y / frame.shape[0])

            x_real, y_real = int(avg_pupil_x * x_ratio), int(avg_pupil_y * y_ratio)

            print(f"Averange: {avg_pupil_x}, {avg_pupil_y}")
            print(f"Screen: {screen_x}, {screen_y}")
            print(f"Real: {x_real}, {y_real}")
            print("------------------")

            # Muovi il cursore
            pyautogui.moveTo(x_real, y_real)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
