import cv2
import mediapipe as mp
import time
import math
from multiprocessing import Queue # Importa Queue per la comunicazione tra processi

# Inizializza MediaPipe Hands
mp_hands = mp.solutions.hands
# Configura il modello MediaPipe Hands
# min_detection_confidence: confidenza minima per la rilevazione della mano
# min_tracking_confidence: confidenza minima per il tracciamento della mano
# max_num_hands: numero massimo di mani da rilevare (qui 1 per semplicità, ma si potrebbe filtrare per mano destra)
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1 # Considera una sola mano per semplificare il tracciamento del cursore
)
mp_drawing = mp.solutions.drawing_utils # Utilità per disegnare i landmark

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

    # Inizializza la cattura video (0 per la webcam predefinita)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hand Tracker: Errore: Impossibile accedere alla telecamera.")
        output_queue.put((0, 0, False)) # Invia un dato di default in caso di errore
        return

    # Ottieni la risoluzione della telecamera per il mapping delle coordinate
    cam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Hand Tracker: Risoluzione telecamera: {cam_width}x{cam_height}")

    # Variabili per il controllo del click (per evitare click continui)
    is_clicking = False
    last_click_time = time.time()
    click_debounce_time = 0.5 # Tempo minimo tra un click e l'altro in secondi

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Hand Tracker: Impossibile leggere il frame dalla telecamera. Uscita.")
                break

            # Capovolgi il frame orizzontalmente per un'esperienza più intuitiva (mirroring)
            frame = cv2.flip(frame, 1)
            # Converti il frame BGR in RGB, richiesto da MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Processa il frame per rilevare le mani
            results = hands.process(rgb_frame)

            cursor_x, cursor_y = oled_width // 2, oled_height // 2 # Posizione di default
            click_state = False

            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Disegna i landmark sul frame (per debugging visivo)
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Determina se è la mano destra
                    # multi_handedness contiene la classificazione (destra/sinistra)
                    if results.multi_handedness and hand_idx < len(results.multi_handedness):
                        handedness_label = results.multi_handedness[hand_idx].classification[0].label
                        # print(f"Hand Tracker: Rilevata mano: {handedness_label}") # Per debugging

                        if handedness_label == 'Right':
                            # --- Calcolo posizione cursore (punta dell'indice) ---
                            # Le coordinate dei landmark sono normalizzate (0.0 a 1.0)
                            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                            
                            # Mappa le coordinate normalizzate alla risoluzione della telecamera
                            cam_x = int(index_finger_tip.x * cam_width)
                            cam_y = int(index_finger_tip.y * cam_height)

                            # Mappa le coordinate della telecamera alla risoluzione OLED
                            cursor_x = int(cam_x * (oled_width / cam_width))
                            cursor_y = int(cam_y * (oled_height / cam_height))
                            
                            # Assicurati che le coordinate siano all'interno dei limiti del display OLED
                            cursor_x = max(0, min(oled_width - 1, cursor_x))
                            cursor_y = max(0, min(oled_height - 1, cursor_y))

                            # --- Rilevamento click (chiusura del pugno) ---
                            # Un metodo per rilevare il pugno chiuso è controllare se le punte delle dita
                            # sono "sotto" (cioè, hanno una coordinata Y maggiore nell'immagine)
                            # rispetto alle loro basi (articolazioni MCP).
                            # Considera un offset per rendere il rilevamento più tollerante.
                            flex_threshold = 0.05 # Soglia di flessione (valore normalizzato)

                            is_index_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > 
                                               hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y + flex_threshold)
                            is_middle_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > 
                                                hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y + flex_threshold)
                            is_ring_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > 
                                              hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y + flex_threshold)
                            is_pinky_flexed = (hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y > 
                                               hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y + flex_threshold)
                            
                            # Il pollice è più complesso. Per semplicità, possiamo basarci principalmente sulle altre dita
                            # o controllare la distanza tra punta del pollice e base dell'indice per un "pizzico"
                            # Ma la richiesta è "chiudere e aprire il pugno".
                            
                            # Se tutte e 4 le dita principali sono flesse, consideriamo il pugno chiuso.
                            current_fist_state = is_index_flexed and is_middle_flexed and is_ring_flexed and is_pinky_flexed
                            
                            # Debouncing del click per evitare click multipli rapidi
                            if current_fist_state and not is_clicking and (time.time() - last_click_time > click_debounce_time):
                                click_state = True
                                is_clicking = True
                                last_click_time = time.time()
                                print("Hand Tracker: CLICK RILEVATO (Pugno Chiuso)")
                            elif not current_fist_state and is_clicking:
                                is_clicking = False # Reset lo stato del click quando il pugno si riapre

            # Invia i dati alla coda
            output_queue.put((cursor_x, cursor_y, click_state))

            # Visualizza il frame con i landmark (per debugging)
            # Puoi commentare queste righe se non hai bisogno di una finestra di visualizzazione
            # cv2.imshow('Hand Tracking', frame)
            
            # Esci se viene premuto 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Hand Tracker: 'q' premuto. Uscita.")
                break

    except Exception as e:
        print(f"Hand Tracker: Errore critico nel loop: {e}")
    finally:
        # Rilascia la telecamera e distruggi tutte le finestre OpenCV
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Hand Tracker: Tracciamento mano terminato.")

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test
    # In un'applicazione reale, output_queue verrebbe passato dal processo principale
    test_queue = Queue()
    # Puoi specificare le dimensioni desiderate per il display OLED per i test
    start_hand_tracking(test_queue, oled_width=128, oled_height=64)

    # Questo blocco è solo per mostrare che la coda riceve dati
    # In un'applicazione reale, un altro processo leggerebbe da questa coda
    try:
        while True:
            if not test_queue.empty():
                data = test_queue.get()
                print(f"Hand Tracker Test: Dati ricevuti da coda: {data}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Test di Hand Tracker interrotto.")

