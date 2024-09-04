from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from time import sleep, localtime
from ble_references import Client


serial = spi(device=0, port=0)
device = ssd1309(serial)
device_width = device.width
device_height = device.height

display_elements = []

cursor_coordinates = (0, 0)
cursor_radius = min(device_width, device_height) // 4

ble = None
ble_f = False


def ble_connect():
    global ble, ble_f
    try:
        ble = Client.connect()
        ble_f = True

    except Exception:
        ble_f = False


def redraw_display():

    with canvas(device) as draw:

        for element in display_elements:
            
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])

            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'])

            elif element['type'] == 'ellipse':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])


def display_clear():
    global display_elements

    device.clear()
    display_elements = []


def add_rectangle(bbox, outline="white", fill="black"):
    display_elements.append({'type': 'rectangle', 'bbox': bbox, 'outline': outline, 'fill': fill})
    redraw_display()


def add_text(position, text, fill="white"):
    display_elements.append({'type': 'text', 'position': position, 'text': text, 'fill': fill})
    redraw_display()


def add_ellipse(bbox, outline="white", fill="black"):
    display_elements.append({'type': 'ellipse', 'bbox': bbox, 'outline': outline, 'fill': fill})
    redraw_display()


def cursor_handler(dx, dy):
    x = cursor_coordinates[0] + dx
    y = cursor_coordinates[1] + dy
    add_ellipse((x - cursor_radius, y - cursor_radius, x + cursor_radius, y + cursor_radius), outline="white", fill=None)
    cursor_coordinates = (x, y)


def ble_receive():

    if ble_f:
        data = Client.receive(ble)

        if data != "None":

            if data[0] == "notes":
                ble_notes(data[1])
                
            elif data[0] == "web":
                ble_web(data[1])

            elif data[0] == "d_coordinates":
                cursor_handler(data[1], data[2])


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


def clock():
    
    current_hour = localtime().tm_hour
    current_min = localtime().tm_min
    current_sec = localtime().tm_sec

    if current_hour < 10:
        current_hour = "0" + str(current_hour)

    current_time = f"{current_hour}:{current_min}"

    add_text((0, 0), current_time, fill="white")
        

def main():

    global display_elements
    
    initializing()

    display_clear()

    while True:

        # In questo modo continuerà a provare a connettersi fino a quando non ci riuscirà
        if not ble_f:
            ble_connect()

        ble_receive()
        clock()

        sleep(1)
        display_clear()


if __name__ == "__main__":
    main()
