import time
import keyboard
from luma.core.interface.serial import spi
from luma.oled.device import ssd1309
from luma.core.render import canvas
from PIL import ImageFont

# Configurazione SPI
serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)

# Inizializza display
device = ssd1309(serial, width=128, height=64, rotate=0)

# Font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)

print("Premi 'q' per uscire")

counter = 0
while True:
    # Disegna sul display
    with canvas(device) as draw:
        draw.text((10, 20), f"Contatore: {counter}", font=font_small, fill=255)
    
    time.sleep(1)
    counter += 1

    # Controlla se è stato premuto q
    if keyboard.is_pressed("q"):
        print("Hai premuto q, chiudo...")
        break

# Pulizia finale (schermo vuoto)
device.clear()
