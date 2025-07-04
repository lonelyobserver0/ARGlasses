from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
from time import sleep

# --- Configurazione del Display ---
# Questi valori (device=0, port=0) sono comuni per Raspberry Pi.
# Assicurati che corrispondano alla tua configurazione hardware.

# Prova a cambiare questi valori se il display non si accende.
# device=0 (SPI0) è il bus SPI più comune.
# port=0 (CE0) e port=1 (CE1) sono i due pin Chip Enable su SPI0.
# Se hai un Raspberry Pi 4 o 5, potresti avere anche SPI1 (device=1).

SPI_DEVICE = 0 # Di solito 0 per SPI0
SPI_PORT = 0   # Prova 0 o 1 (CE0 o CE1)

serial_interface = spi(device=SPI_DEVICE, port=SPI_PORT)

# --- Test di Inizializzazione del Display ---
try:
    print(f"Test Display: Tentativo di inizializzazione con SPI device={SPI_DEVICE}, port={SPI_PORT}...")
    
    # Tenta di creare un'istanza del dispositivo OLED
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
        draw.text((5, 20), f"SPI: {SPI_DEVICE},{SPI_PORT}", fill="white", font=font) # Mostra la configurazione usata
        draw.line((0, 0, device.width, device.height), fill="white") # Linea diagonale
        draw.ellipse((device.width // 4, device.height // 4, 
                      device.width * 3 // 4, device.height * 3 // 4), outline="white") # Ellisse al centro

    sleep(3) # Lascia il tempo all'utente di vedere gli elementi

    # --- Pulizia del Display ---
    print("Test Display: Pulizia del display...")
    device.clear()
    print("Test Display: Display pulito. Test completato con successo.")

except IOError as e:
    print(f"Test Display: ERRORE: Impossibile inizializzare il display OLED con device={SPI_DEVICE}, port={SPI_PORT}.")
    print(f"Test Display: Causa probabile: {e}")
    print("Test Display: 1. Controlla il cablaggio del display (SPI).")
    print("Test Display: 2. Assicurati che l'interfaccia SPI sia abilitata sul tuo Raspberry Pi (sudo raspi-config).")
    print("Test Display: 3. Verifica i permessi utente per accedere ai dispositivi SPI.")
    print("Test Display: 4. Prova a cambiare i valori di SPI_DEVICE e SPI_PORT nello script.")
except Exception as e:
    print(f"Test Display: Si è verificato un errore inatteso: {e}")
finally:
    # Assicurati che il display sia pulito anche in caso di errore non gestito
    if 'device' in locals():
        device.clear()

