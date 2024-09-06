import cv2
import numpy as np
import pyautogui

# Carica il modello di rete neurale per la rilevazione delle mani
net = cv2.dnn.readNetFromTensorflow('models/ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb', 'models/ssd_mobilenet_v1_coco_2017_11_17/ssd_mobilenet_v1_coco.pbtxt')

# Inizializza le variabili per il tracciamento del dito destro
right_hand_x, right_hand_y = 0, 0
right_hand_moved = False

# Inizializza le variabili per il click sinistro del mouse
left_hand_closed = False

# Apri la videocamera
cap = cv2.VideoCapture(0)

while True:
    # Leggi un frame dalla videocamera
    ret, frame = cap.read()

    # Ridimensiona il frame e convertelo in bianco e nero
    frame = cv2.resize(frame, (300, 300))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Esegui la rilevazione delle mani sul frame
    blob = cv2.dnn.blobFromImage(gray, 1.0 / 255, (300, 300), (0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    output = net.forward()

    # Trova la posizione del dito destro
    confidence = output[0, 8, :, 2]
    idx = np.argmax(confidence)
    if confidence[idx] > 0.5:
        x, y = output[0, 8, idx, 3:5] * np.array([frame.shape[1], frame.shape[0]])
        right_hand_x, right_hand_y = int(x), int(y)
        right_hand_moved = True
    else:
        right_hand_moved = False

    # Trova la posizione della mano sinistra
    confidence = output[0, 12, :, 2]
    idx = np.argmax(confidence)
    if confidence[idx] > 0.5:
        x, y = output[0, 12, idx, 3:5] * np.array([frame.shape[1], frame.shape[0]])
        left_hand_closed = True
    else:
        left_hand_closed = False

    # Sposta il cursore del mouse e simula un click sinistro
    if right_hand_moved:
        pyautogui.moveTo(right_hand_x, right_hand_y)
    if left_hand_closed:
        pyautogui.click(button='left')

    # Visualizza il frame con i risultati
    cv2.imshow('Hand Gesture Control', frame)

    # Interrompi il ciclo con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera le risorse
cap.release()
cv2.destroyAllWindows()