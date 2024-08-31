from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from time import sleep, localtime
from ble_references import Client

serial = spi(device=0, port=0)
device = ssd1309(serial)
device_width = device.width
device_height = device.height

try:
    ble = Client.connect()
    ble_f = True
except Exception:
    ble_f = False


def ble_receive():

    if ble_f:
            data = Client.receive(ble)

            if data != "None":
                ble_notes(data)


def ble_notes(data):

    with canvas(device) as draw:
        
        draw.rectangle((device_width - 50, 10, device_width - 100, 60), outline="white", fill="black")
        draw.text((75, 35), data, fill="white")


def initializing():

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((0, 0), "YoRHa", fill="white", align="center")
        draw.text((0, 0), "For the glory of Mankind", fill="white", align="center")
    sleep(5)

    with canvas(device) as draw:
        device.clear()
        draw.text((0, 0), "Initializing...", fill="white", align="right")
    sleep(3)

    with canvas(device) as draw:
        draw.text((0, 10), "Checking filesystem\nintegrity... OK", fill="white", align="right")
    sleep(3)

    with canvas(device) as draw:
        draw.text((0, 20), "Interlink status... OK", fill="white", align="right")
    sleep(3)

    with canvas(device) as draw:
        draw.text((0, 30), "Primary function status... OK", fill="white", align="right")
    sleep(3)

    with canvas(device) as draw:
        draw.text((0, 30), "Connections status... OK", fill="white", align="right")
    sleep(3)


def clock():
    device.clear()
    current_hour = localtime().tm_hour
    current_min = localtime().tm_min
    current_sec = localtime().tm_sec
    current_time = f"{current_hour}:{current_min}"

    with canvas(device) as draw:
        draw.text((0, 0), current_time, fill="white", align="right")
        
    
def main():

    initializing()

    while True:

        ble_receive()
        clock()

        sleep(1)


if __name__ == "__main__":
    main()
