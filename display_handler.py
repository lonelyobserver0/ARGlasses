from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
from time import sleep, localtime
from ble_references import Client
import sys
import multiprocessing
import argparse
import socket
from typing import Union # Importa Union

from hand_cursor import start_hand_tracking

# --- Configuration ---
try:
    font = ImageFont.truetype("NixieOne.ttf", 10)
except IOError:
    print("NixieOne.ttf font not found. Using default font.")
    font = ImageFont.load_default()

# --- Display Setup ---
serial = spi(device=0, port=0)
device = ssd1309(serial)
device_width = device.width
device_height = device.height

display_elements: list[dict] = []

cursor_coordinates: tuple[int, int] = (device_width // 2, device_height // 2)
cursor_radius: int = min(device_width, device_height) // 8

death_flag: bool = False
ble_client: Union[socket.socket, None] = None # Usa Union
ble_connected_flag: bool = False

# --- BLE Functions ---
def ble_connect() -> None:
    global ble_client, ble_connected_flag
    try:
        print("BLE Client: Attempting to connect...")
        connected_socket = Client.connect()
        if connected_socket:
            ble_client = connected_socket
            ble_connected_flag = True
            print("BLE Client: Connected successfully.")
        else:
            ble_connected_flag = False
            print("BLE Client: Connection failed: Client.connect returned None.")
    except Exception as e:
        ble_connected_flag = False
        print(f"BLE Client: Connection failed (exception): {e}")

def ble_notes(data: str) -> None:
    notes_bbox = (5, device_height - 20, device_width - 5, device_height - 5)
    add_rectangle(notes_bbox, outline="white", fill="black", id="notes_display")
    add_text((notes_bbox[0] + 2, notes_bbox[1] + 2), data, fill="white", id="notes_text")
    print(f"BLE Notes: {data}")

def ble_web(data: str) -> None:
    web_bbox = (5, device_height - 40, device_width - 5, device_height - 25)
    add_rectangle(web_bbox, outline="white", fill="black", id="web_display")
    add_text((web_bbox[0] + 2, web_bbox[1] + 2), data, fill="white", id="web_text")
    print(f"BLE Web Data: {data}")

def ble_receive():
    global ble_connected_flag

    if not ble_client:
        print("BLE Client: Not connected. Cannot receive data.")
        ble_connected_flag = False
        return None

    try:
        received_data_str = Client.receive(ble_client)
        
        if received_data_str is None:
            print("BLE Client: Received no data or disconnected.")
            ble_connected_flag = False
            return None
        
        print(f"BLE Client: Received raw data: {received_data_str}")

        parts = received_data_str.split(',')
        data_type = parts[0].strip().lower()

        if data_type == "notes":
            ble_notes(parts[1].strip())
            return ("notes",)
        elif data_type == "web":
            ble_web(parts[1].strip())
            return ("web",)
        elif data_type == "d_coordinates":
            if len(parts) >= 4:
                try:
                    dx = int(parts[1].strip())
                    dy = int(parts[2].strip())
                    click = parts[3].strip().lower() == 'true'
                    x, y = ble_cursor_handler(dx, dy)
                    return ("coor", x, y, click)
                except ValueError as ve:
                    print(f"BLE Client: Error converting coordinate/click data: {ve}. Data: {received_data_str}")
                    return None
            else:
                print(f"BLE Client: Malformed 'd_coordinates' data: {received_data_str}")
                return None
        else:
            print(f"BLE Client: Unknown data type received: {data_type}")
            return None
    except Exception as e:
        print(f"BLE Client: General error during receive: {e}")
        ble_connected_flag = False
        return None

# --- Display Drawing Functions ---
def redraw_display() -> None:
    with canvas(device) as draw:
        for element in display_elements:
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'], font=font)
            elif element['type'] == 'ellipse':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'circle':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])

def display_clear() -> None:
    global display_elements
    device.clear()
    display_elements = []

def add_element(element_type: str, bbox: Union[tuple, None] = None, position: Union[tuple, None] = None, text: Union[str, None] = None,
                outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None: # Usa Union
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

def add_rectangle(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None: # Usa Union
    add_element('rectangle', bbox=bbox, outline=outline, fill=fill, id=id)

def add_text(position: tuple[int, int], text: str, fill: str = "white", id: Union[str, None] = None) -> None: # Usa Union
    add_element('text', position=position, text=text, fill=fill, id=id)

def add_ellipse(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None: # Usa Union
    add_element('ellipse', bbox=bbox, outline=outline, fill=fill, id=id)

def add_circle(x_center: int, y_center: int, radius: int, outline: str = "white", fill: str = "black", id: Union[str, None] = None) -> None: # Usa Union
    bbox = (x_center - radius, y_center - radius, x_center + radius, y_center + radius)
    add_element('circle', bbox=bbox, outline=outline, fill=fill, id=id)

# --- Cursor Logic ---
def is_within_element(element: dict, x_check: int, y_check: int) -> bool:
    element_type = element['type']
    
    if element_type == 'text':
        x, y = element['position']
        text = element['text']
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        if x <= x_check <= x + text_width and y <= y_check <= y + text_height:
            return True
    
    elif element_type in ['rectangle', 'ellipse', 'circle']:
        x1, y1, x2, y2 = element['bbox']
        if x1 <= x_check <= x2 and y1 <= y_check <= y2:
            if element_type in ['ellipse', 'circle']:
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                a = abs(x2 - x1) / 2
                b = abs(y2 - y1) / 2
                if (a == 0 and x_check != cx) or (b == 0 and y_check != cy):
                    return False
                if (a == 0 or b == 0) or (((x_check - cx)**2) / (a**2) + ((y_check - cy)**2) / (b**2) <= 1):
                    return True
            else:
                return True
    
    return False

def cursor_handler(x_cursor: Union[int, None], y_cursor: Union[int, None], clicked: bool) -> None: # Usa Union
    if x_cursor is None or y_cursor is None:
        return

    for element in display_elements:
        if is_within_element(element, x_cursor, y_cursor):
            if clicked:
                element_id = element.get('id')
                print(f"Cursor: Element clicked: {element_id}")
                if element_id == "Off button":
                    global death_flag
                    death_flag = True
                    print("Cursor: Death flag set. Shutting down...")

def update_cursor_on_display(x: int, y: int) -> None:
    global cursor_coordinates
    cursor_coordinates = (x, y)

    cursor_found = False
    for i, element in enumerate(display_elements):
        if element.get('id') == 'main_cursor':
            bbox = (x - cursor_radius, y - cursor_radius, x + cursor_radius, y + cursor_radius)
            display_elements[i]['bbox'] = bbox
            cursor_found = True
            break
    
    if not cursor_found:
        add_circle(x, y, cursor_radius, outline="white", id="main_cursor")
    
    redraw_display()

def ble_cursor_handler(dx: int, dy: int) -> tuple[int, int]:
    current_x, current_y = cursor_coordinates
    
    new_x = max(0, min(device_width - 1, current_x + dx))
    new_y = max(0, min(device_height - 1, current_y + dy))
    
    update_cursor_on_display(new_x, new_y)
    
    return new_x, new_y

# --- Initializing Sequence ---
def initializing() -> None:
    display_clear()
    add_rectangle(device.bounding_box, outline="white", fill="black")
    
    yorha_text = "YoRHa"
    glory_text = "For the glory\nof Mankind"
    
    yorha_bbox = font.getbbox(yorha_text)
    yorha_width = yorha_bbox[2] - yorha_bbox[0]
    yorha_height = yorha_bbox[3] - yorha_bbox[1]

    glory_bbox = font.getbbox(glory_text)
    glory_width = glory_bbox[2] - glory_bbox[0]
    glory_height = glory_bbox[3] - glory_bbox[1]

    add_text(((device_width - yorha_width) // 2, (device_height // 2) - yorha_height - 2), yorha_text, fill="white")
    add_text(((device_width - glory_width) // 2, (device_height // 2) + 2), glory_text, fill="white")
    
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

# --- GUI Elements ---
def clock() -> None:
    current_time_obj = localtime()
    current_hour = current_time_obj.tm_hour
    current_min = current_time_obj.tm_min
    
    time_str = f"{current_hour:02d}:{current_min:02d}"
    
    add_text((0, 0), time_str, fill="white", id="clock_display")

def death_button() -> None:
    button_text = "OFF"
    button_x, button_y = device_width - font.getbbox(button_text)[2] - 5, 5
    add_text((button_x, button_y), button_text, fill="white", id="Off button")

# --- Main GUI Loop Function ---
def GUI_loop_content(x_cursor: Union[int, None], y_cursor: Union[int, None], click: bool) -> None: # Usa Union
    display_clear()

    death_button()
    clock()

    if x_cursor is not None and y_cursor is not None:
        update_cursor_on_display(x_cursor, y_cursor)

    cursor_handler(x_cursor, y_cursor, click)
    
    sleep(0.05)

# --- Main Application Entry Point ---
def main(queue: Union[multiprocessing.Queue, None] = None, bl_flag: bool = False, cam_flag: bool = False) -> None: # Usa Union
    print("OLED GUI: Application started.")
    
    if cam_flag:
        print("OLED GUI: Running in camera mode.")
        if queue is None:
            print("OLED GUI: Error: Camera mode requires a multiprocessing Queue. Exiting.")
            return
        hand_tracker_process = multiprocessing.Process(
            target=start_hand_tracking,
            args=(queue, device_width, device_height)
        )
        hand_tracker_process.start()
        print("OLED GUI: Hand tracking process started.")

    elif bl_flag:
        print("OLED GUI: Running in Bluetooth mode.")
    else:
        print("OLED GUI: No input mode specified. Please use -bl or -cam. Exiting.")
        return

    initializing()

    current_x_cursor, current_y_cursor, current_click = cursor_coordinates[0], cursor_coordinates[1], False

    while not death_flag:
        if cam_flag:
            try:
                data = queue.get(timeout=0.01)
                current_x_cursor, current_y_cursor, current_click = data
            except multiprocessing.queues.Empty:
                current_click = False
                pass
            except Exception as e:
                print(f"OLED GUI: Error reading from camera queue: {e}")
                current_x_cursor, current_y_cursor, current_click = None, None, False

        elif bl_flag:
            if not ble_connected_flag:
                ble_connect()
                if not ble_connected_flag:
                    sleep(2)
                    continue
            
            ble_result = ble_receive()
            if ble_result:
                if ble_result[0] == "coor":
                    current_x_cursor, current_y_cursor, current_click = ble_result[1], ble_result[2], ble_result[3]
                else:
                    current_click = False
            else:
                current_click = False
            
        GUI_loop_content(current_x_cursor, current_y_cursor, current_click)

    print("OLED GUI: Application shutdown initiated.")
    display_clear()
    add_text((device_width // 2 - 20, device_height // 2 - 5), "Shutting down...", fill="white")
    sleep(2)
    display_clear()
    
    if cam_flag and 'hand_tracker_process' in locals() and hand_tracker_process.is_alive():
        print("OLED GUI: Terminating hand tracking process...")
        hand_tracker_process.terminate()
        hand_tracker_process.join()
        print("OLED GUI: Hand tracking process terminated.")

    if ble_connected_flag and ble_client:
        try:
            Client.close(ble_client)
            print("OLED GUI: BLE client closed.")
        except Exception as e:
            print(f"OLED GUI: Error closing BLE client: {e}")


# --- Main Execution Block ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OLED Display GUI with external input.")
    parser.add_argument("-bl", "--bluetooth", action="store_true", help="Enable Bluetooth input mode.")
    parser.add_argument("-cam", "--camera", action="store_true", help="Enable Camera input mode (requires MediaPipe and OpenCV).")
    
    args = parser.parse_args()

    if args.bluetooth and args.camera:
        print("Error: Please select either Bluetooth (-bl) or Camera (-cam) mode, not both.")
        sys.exit(1)
    if not args.bluetooth and not args.camera:
        print("Error: No input mode specified. Please use -bl or -cam.")
        sys.exit(1)

    camera_queue = None
    if args.camera:
        camera_queue = multiprocessing.Queue()
        print("OLED GUI: Camera mode selected. Camera stream will be processed by hand_tracker.")

    gui_process = multiprocessing.Process(target=main, args=(camera_queue, args.bluetooth, args.camera))
    gui_process.start()
    gui_process.join()

    print("OLED GUI: Main application process terminated.")
