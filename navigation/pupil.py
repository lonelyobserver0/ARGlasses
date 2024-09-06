import cv2
import pyautogui
import numpy as np
import mediapipe as mp

pyautogui.FAILSAFE = False

# Inizializza Mediapipe per il rilevamento della posa degli occhi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# Imposta risoluzione del monitor
screen_width, screen_height = pyautogui.size()

# Dati di calibrazione aggiornati
calibration_data = {
    (420, 40): (0, 0),  # Angolo superiore sinistro
    (378, 32): (screen_width, 0),  # Angolo superiore destro
    (400, 40): (0, screen_height),  # Angolo inferiore sinistro
    (376, 41): (screen_width, screen_height),  # Angolo inferiore destro
    # Aggiungi ulteriori punti per maggiore precisione se necessario
}

def interpolate(pupil_x, pupil_y):
    # Converti i dati di calibrazione in array numpy
    pupil_points = np.array(list(calibration_data.keys()))
    screen_points = np.array(list(calibration_data.values()))

    # Calcola la distanza da ciascun punto di calibrazione
    distances = np.linalg.norm(pupil_points - np.array([pupil_x, pupil_y]), axis=1)

    # Trova i 4 punti di calibrazione più vicini per l'interpolazione
    nearest_indices = np.argsort(distances)[:4]
    nearest_pupil_points = pupil_points[nearest_indices]
    nearest_screen_points = screen_points[nearest_indices]

    # Seleziona i due punti più vicini sull'asse x e i due sull'asse y per interpolazione bilineare
    x_coords = nearest_pupil_points[:, 0]
    y_coords = nearest_pupil_points[:, 1]
    x1, x2 = np.min(x_coords), np.max(x_coords)
    y1, y2 = np.min(y_coords), np.max(y_coords)

    # Evita la divisione per zero assicurandoti che x2 != x1 e y2 != y1
    if x1 == x2 or y1 == y2:
        print("Errore: punti di calibrazione troppo vicini o insufficienti per l'interpolazione.")
        return None

    # Trova i punti corrispondenti sullo schermo
    q11 = nearest_screen_points[(nearest_pupil_points == [x1, y1]).all(axis=1)][0]
    q12 = nearest_screen_points[(nearest_pupil_points == [x1, y2]).all(axis=1)][0]
    q21 = nearest_screen_points[(nearest_pupil_points == [x2, y1]).all(axis=1)][0]
    q22 = nearest_screen_points[(nearest_pupil_points == [x2, y2]).all(axis=1)][0]

    # Interpolazione bilineare
    screen_x = (
        q11[0] * (x2 - pupil_x) * (y2 - pupil_y) +
        q21[0] * (pupil_x - x1) * (y2 - pupil_y) +
        q12[0] * (x2 - pupil_x) * (pupil_y - y1) +
        q22[0] * (pupil_x - x1) * (pupil_y - y1)
    ) / ((x2 - x1) * (y2 - y1))

    screen_y = (
        q11[1] * (x2 - pupil_x) * (y2 - pupil_y) +
        q21[1] * (pupil_x - x1) * (y2 - pupil_y) +
        q12[1] * (x2 - pupil_x) * (pupil_y - y1) +
        q22[1] * (pupil_x - x1) * (pupil_y - y1)
    ) / ((x2 - x1) * (y2 - y1))

    # Verifica se le coordinate sono all'interno del limite dello schermo
    screen_x = np.clip(screen_x, 0, screen_width)
    screen_y = np.clip(screen_y, 0, screen_height)

    return int(screen_x), int(screen_y)

def get_pupil_position(eye_landmarks, frame_shape):
    # Prendi le coordinate degli occhi dal mesh facciale
    x = int(eye_landmarks.x * frame_shape[1])
    y = int(eye_landmarks.y * frame_shape[0])
    return x, y

# Avvia la webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Converti in RGB per mediapipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Utilizza gli indici specifici per l'iride (media di più punti per maggiore precisione)
            left_eye_indices = [468, 469, 470, 471]  # Indici per l'iride sinistra
            right_eye_indices = [473, 474, 475, 476] # Indici per l'iride destra

            # Media dei punti per ottenere una posizione centrale delle pupille
            left_pupil = np.mean([[face_landmarks.landmark[i].x, face_landmarks.landmark[i].y] for i in left_eye_indices], axis=0)
            right_pupil = np.mean([[face_landmarks.landmark[i].x, face_landmarks.landmark[i].y] for i in right_eye_indices], axis=0)

            # Converti le coordinate normalizzate in pixel
            left_pupil_x, left_pupil_y = int(left_pupil[0] * frame.shape[1]), int(left_pupil[1] * frame.shape[0])
            right_pupil_x, right_pupil_y = int(right_pupil[0] * frame.shape[1]), int(right_pupil[1] * frame.shape[0])

            # Calcola la media delle coordinate delle pupille per una stima centrale
            avg_pupil_x = (left_pupil_x + right_pupil_x) / 2
            avg_pupil_y = (left_pupil_y + right_pupil_y) / 2

            # Converti le coordinate delle pupille in coordinate del monitor
            screen_coords = interpolate(avg_pupil_x, avg_pupil_y)

            if screen_coords:
                screen_x, screen_y = screen_coords
                # Stampa per debug
                print(f"Coordinate schermo: {screen_x}, {screen_y}")
                # Muovi il cursore
                pyautogui.moveTo(screen_x, screen_y)

    # Mostra il feed video per il debug
    cv2.imshow("Tracciamento Pupille", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
