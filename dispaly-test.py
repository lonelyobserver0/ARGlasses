from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from time import sleep, localtime
from ble_references import Client

serial = spi(device=0, port=0)
device = ssd1309(serial)
width = device.width
height = device.height

try:
    ble = Client.connect()
    ble_f = True
except OSError:
    ble_f = False


def initializing():
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((30, 40), "YoRHa", fill="white")
        draw.text((10, 50), "Glory to Mankind", fill="white")
        sleep(1.5)
        device.clear()
        draw.text((0, 0), "Initializing...", fill="white", align="right")
        sleep(0.75)
        draw.text((0, 10), "Checking filesystem integrity... OK", fill="white", align="right")
        sleep(0.75)
        draw.text((0, 20), "Interlink status... OK", fill="white", align="right")
        sleep(0.75)
        draw.text((0, 30), "Primary function status... OK", fill="white", align="right")
        sleep(0.75)
        draw.text((0, 30), "Connections status... OK", fill="white", align="right")
        sleep(0.75)


def gui():
    device.clear()
    current_hour = localtime().tm_hour
    current_min = localtime().tm_min
    current_sec = localtime().tm_sec
    current_time = f"{current_hour}:{current_min}"
    with canvas(device) as draw:
        draw.text((0, 0), current_time, fill="white", align="right")


def ble_fun_1(data):
    with canvas(device) as draw:
        draw.rectangle((50, 10, 100, 60), outline="white", fill="black")
        draw.text((75, 35), data, fill="white")


def main():

    initializing()

    while True:

        if ble_f:
            data = Client.receive(ble)
            if data != "None":
                ble_fun_1(data)

        gui()

        sleep(1)


if __name__ == "__main__":
    main()
