from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
from time import sleep

# --- Configurazione del Display ---
# Questi valori (device=0, port=0) sono comuni per Raspberry Pi.
# Assicurati che corrispondano alla tua configurazione hardware.
serial_interface = spi(device=0, port=0)

# --- Test di Inizializzazione del Display ---
try:
    # Tenta di creare un'istanza del dispositivo OLED
    # Se il display non è collegato o SPI non è abilitato, questo fallirà.
    device = ssd1309(serial_interface)
    print("Test Display: Display OLED inizializzato con successo.")
    print(f"Test Display: Larghezza: {device.width} pixel, Altezza: {device.height} pixel")

    # Carica un font di base
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", 10) # Un font comune su sistemi Linux
    except IOError:
        print("Test Display: Font DejaVuSansMono.ttf non trovato. Usando il font di default.")
        font = ImageFont.load_default()

    # --- Test di Disegno sul Display ---
    print("Test Display: Disegno di elementi di prova...")

    # Disegna un rettangolo attorno ai bordi del display
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((5, 5), "Display Test OK!", fill="white", font=font)
        draw.text((5, 20), "Hello, World!", fill="white", font=font)
        draw.line((0, 0, device.width, device.height), fill="white") # Linea diagonale
        draw.ellipse((device.width // 4, device.height // 4, 
                      device.width * 3 // 4, device.height * 3 // 4), outline="white") # Ellisse al centro

    sleep(3) # Lascia il tempo all'utente di vedere gli elementi

    # --- Pulizia del Display ---
    print("Test Display: Pulizia del display...")
    device.clear()
    print("Test Display: Display pulito. Test completato con successo.")

except IOError as e:
    print(f"Test Display: ERRORE: Impossibile inizializzare il display OLED.")
    print(f"Test Display: Causa probabile: {e}")
    print("Test Display: 1. Controlla il cablaggio del display (SPI).")
    print("Test Display: 2. Assicurati che l'interfaccia SPI sia abilitata sul tuo Raspberry Pi (sudo raspi-config).")
    print("Test Display: 3. Verifica i permessi utente per accedere ai dispositivi SPI.")
except Exception as e:
    print(f"Test Display: Si è verificato un errore inatteso: {e}")
finally:
    # Assicurati che il display sia pulito anche in caso di errore non gestito
    if 'device' in locals():
        device.clear()

