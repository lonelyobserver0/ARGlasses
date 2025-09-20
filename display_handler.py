from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont

# --- Font Setup ---
try:
    font = ImageFont.truetype("NixieOne.ttf", 10)
except IOError:
    print("NixieOne.ttf font not found. Using default font.")
    font = ImageFont.load_default()

# --- Display Setup ---
serial = spi(device=0, port=0, gpio_DC=25, gpio_RST=27)
device = ssd1309(serial, width=128, height=64, rotate=0)
device_width = device.width
device_height = device.height

# --- Display Elements Storage ---
from typing import Union
display_elements: list[dict] = []

# --- Drawing Functions ---
def redraw_display() -> None:
    with canvas(device) as draw:
        for element in display_elements:
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'], font=font)
            elif element['type'] in ['ellipse', 'circle']:
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])

def display_clear() -> None:
    global display_elements
    device.clear()
    display_elements = []

def add_element(element_type: str, bbox: Union[tuple, None] = None,
                position: Union[tuple, None] = None, text: Union[str, None] = None,
                outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None:
    new_element = {
        'type': element_type,
        'bbox': bbox,
        'position': position,
        'text': text,
        'outline': outline,
        'fill': fill,
        'id': id
    }
    display_elements.append(new_element)
    redraw_display()

def add_rectangle(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None:
    add_element('rectangle', bbox=bbox, outline=outline, fill=fill, id=id)

def add_text(position: tuple[int, int], text: str, fill: str = "white", id: Union[str, None] = None) -> None:
    add_element('text', position=position, text=text, fill=fill, id=id)

def add_ellipse(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None:
    add_element('ellipse', bbox=bbox, outline=outline, fill=fill, id=id)

def add_circle(x_center: int, y_center: int, radius: int, outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None:
    bbox = (x_center - radius, y_center - radius, x_center + radius, y_center + radius)
    add_element('circle', bbox=bbox, outline=outline, fill=fill, id=id)

# --- Example Usage ---
if __name__ == '__main__':
    display_clear()
    
    add_rectangle((0, 0, device_width, device_height), outline="white", fill="black")
    add_text((10, 10), "Hello OLED!", fill="white", id="greeting")
    add_circle(device_width//2, device_height//2, 10, outline="white", fill="black", id="center_circle")
    add_ellipse((20, 40, 60, 60), outline="white", fill="black", id="ellipse_example")
