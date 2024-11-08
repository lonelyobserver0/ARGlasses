from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
from time import sleep, localtime
from ble_references import Client
import sys
import multiprocessing

font = ImageFont.truetype("NixieOne.ttf", 1)

bl_f, cam_f = False, False  # Inizializzando le flag degli argomenti
for cli_argument in sys.argv:
    if cli_argument == "-bl":
        bl_f = True
    elif cli_argument == "-cam":
        cam_f = True

serial = spi(device=0, port=0)
device = ssd1309(serial)
device_width = device.width
device_height = device.height

display_elements = []

cursor_coordinates = (0, 0)
cursor_radius = min(device_width, device_height) // 4

death_flag = False

ble = None
ble_f = False


def ble_connect():
    global ble, ble_f
    try:
        ble = Client.connect()
        ble_f = True

    except Exception:
        ble_f = False


# region Display
def redraw_display():

    with canvas(device) as draw:

        for element in display_elements:
            
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])

            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'], font=font)

            elif element['type'] == 'ellipse':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])

            elif element['type'] == 'circle':
                draw.circle(element['bbox'], outline=element['outline'], fill=element['fill'])


def display_clear():
    global display_elements

    device.clear()
    display_elements = []


def add_rectangle(bbox, outline="white", fill="black", id=None):
    display_elements.append({'type': 'rectangle', 'bbox': bbox, 'outline': outline, 'fill': fill, 'id': id})
    redraw_display()


def add_text(position, text, fill="white", id=None):
    display_elements.append({'type': 'text', 'position': position, 'text': text, 'fill': fill, 'id': id})
    redraw_display()


def add_ellipse(bbox, outline="white", fill="black", id=None):
    display_elements.append({'type': 'ellipse', 'bbox': bbox, 'outline': outline, 'fill': fill, 'id': id})
    redraw_display()


def add_circle(bbox, outline="white", fill="black", id=None):   # bbox = (x_centro, y_centro, radius)
    display_elements.append({'type': 'ellipse', 'bbox': bbox, 'outline': outline, 'fill': fill, 'id': id})
    redraw_display()

# endregion


# region Cursor
def is_within_element(element, x_check, y_check):
    element_type = element['type']
    
    if element_type == 'text':
        x, y = element['position']
        text = element['text']
        font = element.get('font', ImageFont.load_default())
        text_width, text_height = font.getsize(text)
        # Verifica se le coordinate sono all'interno del testo
        if x <= x_check <= x + text_width and y <= y_check <= y + text_height:
            return True
    
    elif element_type == 'rectangle':
        x1, y1, x2, y2 = element['bbox']
        # Verifica se le coordinate sono all'interno del rettangolo
        if x1 <= x_check <= x2 and y1 <= y_check <= y2:
            return True
    
    elif element_type == 'circle':
        cx, cy, radius = element['bbox']
        # Calcola la distanza del punto dal centro del cerchio
        if (x_check - cx) ** 2 + (y_check - cy) ** 2 <= radius ** 2:
            return True
    
    elif element_type == 'ellipse':
        # Due coppie di coordinate (bounding box)
        x1, y1, x2, y2 = element['bbox']
        # Calcola il centro dell'ellisse
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        # Calcola i semiassi
        a = abs(x2 - x1) / 2
        b = abs(y2 - y1) / 2
        # Verifica se il punto è all'interno dell'ellisse usando l'equazione dell'ellisse
        if ((x_check - cx) ** 2) / (a ** 2) + ((y_check - cy) ** 2) / (b ** 2) <= 1:
            return True
    
    return False


def cursor_handler(x, y, clicked):
    
    for element in display_elements:
        fs = is_within_element(element, x, y)
        if fs:
            # Do something with the focus trigger
            if clicked:
                if element['id'] == "Off button":
                    global death_flag
                    death_flag = True
                # elif tutti gli altri bottoni ...


def ble_cursor_handler(dx, dy):
    global cursor_coordinates
    x = cursor_coordinates[0] + dx
    y = cursor_coordinates[1] + dy
    add_ellipse((x - cursor_radius, y - cursor_radius, x + cursor_radius, y + cursor_radius), outline="white")
    cursor_coordinates = (x, y)
    return x, y

# endregion


def ble_notes(data):
        
    add_rectangle((device_width - 50, 10, device_width - 100, 60), outline="white", fill="black")
    add_text((75, 35), data, fill="white")


def ble_web(data):
        
    add_rectangle((device_width - 50, 10, device_width - 100, 60), outline="white", fill="black")
    add_text((75, 35), data, fill="white")


def initializing():

    add_rectangle(device.bounding_box, outline="white", fill="black")
    add_text(((device_width / 2) -10, (device_height / 2) -5), "YoRHa", fill="white")
    add_text(((device_width / 2) -30, (device_height / 2) +5), "For the glory\nof Mankind", fill="white")
    add_text(((device_width / 2) -10, (device_height / 2) +10), "of Mankind", fill="white")
    sleep(4)
    
    display_clear()
    add_text((0, 0), "Initializing...", fill="white")
    sleep(2)

    add_text((0, 20), "Checking filesystem\nintegrity... OK", fill="white")
    sleep(2)

    display_clear()
    add_text((0, 0), "Interlink status... OK", fill="white")
    sleep(2)
    
    add_text((0, 20), "Primary function\nstatus... OK", fill="white")
    sleep(2)

    display_clear()
    add_text((0, 0), "Connections status... OK", fill="white")
    sleep(2)
    
    display_clear()


def clock():
    
    current_hour = localtime().tm_hour
    current_min = localtime().tm_min
    current_sec = localtime().tm_sec

    if current_hour < 10:
        current_hour = "0" + str(current_hour)

    current_time = f"{current_hour}:{current_min}"

    add_text((0, 0), current_time, fill="white")
        

def death_button():
    add_text((5, 5), "CTB", fill="white", id="Off button")
    

def ble_receive():

    data = Client.receive(ble)

    if data != "None":

        if data[0] == "notes":
            ble_notes(data[1])
            return ("notes")
                
        elif data[0] == "web":
            ble_web(data[1])
            return ("web")

        elif data[0] == "d_coordinates":
            x, y = ble_cursor_handler(data[1], data[2])
            click = data[3]
            return ("coor", x, y, click)


def GUI(x, y, click):
    death_button()
    clock()

    cursor_handler(x, y, click)
    sleep(1)
    display_clear()

# region Main


def main(queue):
    
    if cam_f:
        # Modalità con camera
        print("Avviato con camera")
        
    elif bl_f:
        # Modalità con bluetooth
        print("Avviato con bluetooth")

    else:
        print("Expected at least 1 argument, got 0")
        
    print("-->Avvio senza modalità di input<--")
    
    initializing()

    # region Simulacri
    """
    while True:
        
        if cam_f:
            x_cursor, y_cursor = None, None # Le coordinate calcolate dal file cursor_handler.py --> Praticamente gli elementi della queue del multiprocessing
            click = None #Flag dal file cursor_handler.py                                        --> Praticamente gli elementi della queue del multiprocessing
        
        if bl_f:
            if not ble_f:
                ble_connect()
                
            else:
                ble_result = ble_receive()
                
                if ble_result[0] == "coor":
                    x_cursor, y_cursor = ble_result[1], ble_result[2]
                    click = ble_result[3]
        
        death_button()
        clock()

        cursor_handler(x_cursor, y_cursor, click)
        sleep(1)
        display_clear()
        
        if death_flag:
            break
    """
    # endregion

    x_cursor, y_cursor = None, None
    click = None
    
    while cam_f:
        data = queue.get()
        # Le coordinate calcolate dal file cursor_handler.py
        # --> Praticamente gli elementi della queue del multiprocessing
        x_cursor, y_cursor, click = data
        GUI(x_cursor, y_cursor, click)
        
        if death_flag:
            break
    
    while bl_f:
        
        if not ble_f:
            ble_connect()
                
        else:
            ble_result = ble_receive()
                
            if ble_result[0] == "coor":
                x_cursor, y_cursor = ble_result[1], ble_result[2]
                click = ble_result[3]
        
        GUI(x_cursor, y_cursor, click)
        
        if death_flag:
            break
# endregion


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    p2 = multiprocessing.Process(target=main, args=(queue,))
    p2.start()
    p2.join()
