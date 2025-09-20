import time
import curses
from luma.core.interface.serial import spi
from luma.oled.device import ssd1309
from luma.core.render import canvas
from PIL import ImageFont

def main(stdscr):
    # Configurazione SPI
    serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
    device = ssd1309(serial, width=128, height=64, rotate=0)

    # Font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)

    curses.curs_set(0)          # Nasconde il cursore
    stdscr.nodelay(True)        # Non blocca su getch()
    stdscr.addstr(0, 0, "Premi q per uscire")
    stdscr.refresh()

    counter = 0
    while True:
        # Disegna sul display
        with canvas(device) as draw:
            draw.text((10, 20), f"Contatore: {counter}", font=font, fill=255)

        time.sleep(1)
        counter += 1

        # Controllo pressione tasto
        c = stdscr.getch()
        if c == ord("q"):
            break

    # Pulizia schermo OLED
    device.clear()

curses.wrapper(main)
