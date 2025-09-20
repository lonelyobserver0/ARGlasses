import time
import threading
from luma.core.interface.serial import spi
from luma.oled.device import ssd1309
from luma.core.render import canvas
from PIL import ImageFont

# Variabile di controllo
running = True

def input_thread():
    global running
    while running:
        key = input("Premi q e Invio per uscire: ")
        if key.strip().lower() == "q":
            running = False
            break

# Avvia il thread che ascolta la tastiera
thread = threading.Thread(target=input_thread, daemon=True)
thread.start()

# Configurazione SPI
serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
device = ssd1309(serial, width=128, height=64, rotate=0)

# Font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 2)

#------------------------------#

counter = 0
while running:
    with canvas(device) as draw:
        draw.text((10, 20), f"Contatore: {counter}", font=font, fill=255)

    time.sleep(1)
    counter += 1

# Pulizia finale schermo
device.clear()
print("Uscito dal programma.")
