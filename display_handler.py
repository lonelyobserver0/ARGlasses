import time
from luma.core.interface.serial import spi
from luma.oled.device import ssd1309
from luma.core.render import canvas
from PIL import ImageFont

# Configurazione SPI
# cs=0 significa CE0, se usi CE1 metti cs=1
serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)

# Inizializza display SSD1309
device = ssd1309(serial, width=128, height=64, rotate=0)

# Usa un font di sistema
font = ImageFont.load_default()
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)

# Disegna qualcosa
with canvas(device) as draw:
    draw.text((10, 20), "Hello Waveshare!", font=font, fill=255)

time.sleep(20)

# Pulizia: schermo vuoto
with canvas(device) as draw:
    pass
