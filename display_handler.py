import time
from luma.core.interface.serial import spi
from luma.oled.device import ssd1309
from luma.core.render import canvas
from PIL import ImageFont


# Configurazione SPI
serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
device = ssd1309(serial, width=128, height=64, rotate=0)

# Font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 6)

#------------------------------#

counter = 0
while True:
    with canvas(device) as draw:
        draw.text((10, 20), f"Contatore: {counter}", font=font, fill=255)

    time.sleep(1)
    counter += 1

# Pulizia finale schermo
device.clear()
print("Uscito dal programma.")
