from p5 import *
from time import time, sleep
from GUI.base import *
from GUI.clock import draw_clock
from GUI.BLE import ble_input
from GUI.cam import cam_input

# Fallback font loader
def get_default_font():
    return create_font("Arial", 32) or create_font("sans-serif", 32)

font = get_default_font()

def draw_text(text, x, y, size=32, color=(255, 255, 255), anchor_x=LEFT, anchor_y=TOP, font=font, id=None):
    text_font(font)
    text_size(size)
    fill(*color)
    text_align(anchor_x, anchor_y)
    text(text, (x, y), id=id)

def draw_button(x, y, w, h, label, id_prefix="button"):
    add_rectangle(x, y, w, h, color=(255, 0, 0), id=f"{id_prefix} rect")
    draw_text(label, x + w / 2, y + h / 2, size=20, color=(255, 255, 255), anchor_x=CENTER, anchor_y=CENTER, id=f"{id_prefix} text")

def death_button():
    draw_button(10, 10, 80, 40, "OFF", id_prefix="Off button")

def clock():
    draw_clock(250, 250, radius=100)

def update_gui_state(x_cursor, y_cursor, click):
    elements_to_remove = [
        "Off button rect",
        "Off button text",
        "clock",
        "status",
        "cursor",
        "click_label"
    ]
    for eid in elements_to_remove:
        display_remove(eid)

def render_gui(x_cursor=None, y_cursor=None, click=False):
    death_button()
    clock()
    draw_text("Sistema attivo", 100, 20, size=24, color=(255, 255, 255), id="status")
    if x_cursor is not None and y_cursor is not None:
        add_ellipse(x_cursor, y_cursor, 20, 20, color=(0, 255, 0), id="cursor")
        if click:
            draw_text("Click!", x_cursor + 10, y_cursor, size=16, color=(255, 255, 0), id="click_label")

def handle_click(x, y):
    # Coordinate del bottone OFF
    if 10 <= x <= 90 and 10 <= y <= 50:
        print("Shutting down...")
        exit(0)

def GUI(x_cursor=None, y_cursor=None, click=False):
    update_gui_state(x_cursor, y_cursor, click)
    render_gui(x_cursor, y_cursor, click)
    if click and x_cursor is not None and y_cursor is not None:
        handle_click(x_cursor, y_cursor)

def main_cam():
    print("Running with cam input")
    while True:
        x, y, click = cam_input()
        GUI(x, y, click)
        sleep(1 / 30)  # ~30 FPS

def main_ble():
    print("Running with BLE input")
    while True:
        x, y, click = ble_input()
        GUI(x, y, click)
        sleep(1 / 30)  # ~30 FPS

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 run.py [cam|ble|test]")
        return
    mode = sys.argv[1]
    if mode == "cam":
        main_cam()
    elif mode == "ble":
        main_ble()
    elif mode == "test":
        while True:
            GUI(100, 100, click=True)
            sleep(1 / 2)
    else:
        print("Unknown mode")

if __name__ == '__main__':
    main()
