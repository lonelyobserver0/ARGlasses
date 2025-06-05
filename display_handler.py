from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
from time import sleep, localtime
from ble_references import Client # Import the Client class from your updated module
import sys
import multiprocessing
import argparse # For better command-line argument parsing
import socket # Required for socket type hinting

# --- Configuration ---
# Font for display text. Ensure 'NixieOne.ttf' is in the same directory or provide a full path.
try:
    font = ImageFont.truetype("NixieOne.ttf", 10) # Changed font size for better visibility
except IOError:
    print("NixieOne.ttf font not found. Using default font.")
    font = ImageFont.load_default()

# --- Display Setup ---
# Initialize SPI interface and SSD1309 OLED device
# These values (device=0, port=0) are common for Raspberry Pi, adjust if needed.
serial = spi(device=0, port=0)
device = ssd1309(serial)
device_width = device.width
device_height = device.height

# List to hold elements to be drawn on the display
display_elements: list[dict] = []

# Cursor properties
cursor_coordinates: tuple[int, int] = (device_width // 2, device_height // 2) # Start cursor in center
cursor_radius: int = min(device_width, device_height) // 8 # Increased radius for better visibility

# Global flags and BLE client instance
death_flag: bool = False
ble_client: socket.socket | None = None # This will hold the connected Bluetooth client socket
ble_connected_flag: bool = False # Flag to track BLE connection status

# --- BLE Functions ---
def ble_connect() -> None:
    """
    Attempts to connect to the BLE client using the Client class from ble_references.
    Updates the global ble_client and ble_connected_flag.
    """
    global ble_client, ble_connected_flag
    try:
        print("Attempting to connect to BLE client...")
        # Client.connect now returns the socket or None
        connected_socket = Client.connect()
        if connected_socket:
            ble_client = connected_socket
            ble_connected_flag = True
            print("BLE connected successfully.")
        else:
            ble_connected_flag = False
            print("BLE connection failed: Client.connect returned None.")
    except Exception as e:
        ble_connected_flag = False
        print(f"BLE connection failed (exception): {e}")

def ble_notes(data: str) -> None:
    """Displays notes received via BLE on the screen."""
    # Define a clear area for notes display at the bottom of the screen
    notes_bbox = (5, device_height - 20, device_width - 5, device_height - 5)
    add_rectangle(notes_bbox, outline="white", fill="black", id="notes_display")
    add_text((notes_bbox[0] + 2, notes_bbox[1] + 2), data, fill="white", id="notes_text")
    print(f"BLE Notes: {data}")

def ble_web(data: str) -> None:
    """Displays web data received via BLE on the screen."""
    # Define a clear area for web data display, above notes
    web_bbox = (5, device_height - 40, device_width - 5, device_height - 25)
    add_rectangle(web_bbox, outline="white", fill="black", id="web_display")
    add_text((web_bbox[0] + 2, web_bbox[1] + 2), data, fill="white", id="web_text")
    print(f"BLE Web Data: {data}")

def ble_receive():
    """
    Receives data from the BLE client using the Client class from ble_references.
    Processes received data and returns relevant information for GUI updates.
    """
    global ble_connected_flag # Need to modify this if client disconnects

    if not ble_client:
        print("BLE client not connected. Cannot receive data.")
        ble_connected_flag = False # Ensure flag is false if client is None
        return None

    try:
        # Client.receive now returns Optional[str]
        received_data_str = Client.receive(ble_client)
        
        if received_data_str is None:
            # This indicates disconnection or no data
            print("BLE client received no data or disconnected.")
            ble_connected_flag = False # Update connection status
            return None
        
        print(f"Received raw BLE data: {received_data_str}") # Print raw data for debugging

        # Assuming data format is "type,value1,value2,..."
        parts = received_data_str.split(',')
        data_type = parts[0].strip().lower() # Normalize type string

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
                    # Convert 'true'/'false' string to boolean
                    click = parts[3].strip().lower() == 'true'
                    x, y = ble_cursor_handler(dx, dy)
                    return ("coor", x, y, click)
                except ValueError as ve:
                    print(f"Error converting coordinate/click data: {ve}. Data: {received_data_str}")
                    return None
            else:
                print(f"Malformed 'd_coordinates' data: {received_data_str}")
                return None
        else:
            print(f"Unknown BLE data type received: {data_type}")
            return None
    except Exception as e:
        print(f"General error during BLE receive: {e}")
        ble_connected_flag = False # Assume disconnection on general error
        # Consider calling Client.close(ble_client) here to clean up
        return None

# --- Display Drawing Functions ---
def redraw_display() -> None:
    """Clears the display and redraws all elements from the display_elements list."""
    with canvas(device) as draw:
        for element in display_elements:
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'], font=font)
            elif element['type'] == 'ellipse':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'circle': # Circles are drawn using ellipse with equal axes
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])

def display_clear() -> None:
    """Clears all elements from the internal list and the physical display."""
    global display_elements
    device.clear()
    display_elements = []

def add_element(element_type: str, bbox: tuple = None, position: tuple = None, text: str = None,
                outline: str = "white", fill: str = "black", id: str = None) -> None:
    """
    Adds a new drawing element to the display_elements list.
    Redraws the display immediately.
    """
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

def add_rectangle(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: str = None) -> None:
    """Adds a rectangle element."""
    add_element('rectangle', bbox=bbox, outline=outline, fill=fill, id=id)

def add_text(position: tuple[int, int], text: str, fill: str = "white", id: str = None) -> None:
    """Adds a text element."""
    add_element('text', position=position, text=text, fill=fill, id=id)

def add_ellipse(bbox: tuple[int, int, int, int], outline: str = "white", fill: str = "black", id: str = None) -> None:
    """Adds an ellipse element."""
    add_element('ellipse', bbox=bbox, outline=outline, fill=fill, id=id)

def add_circle(x_center: int, y_center: int, radius: int, outline: str = "white", fill: str = "black", id: str = None) -> None:
    """
    Adds a circle element.
    bbox is calculated from (x_center, y_center, radius).
    """
    bbox = (x_center - radius, y_center - radius, x_center + radius, y_center + radius)
    add_element('circle', bbox=bbox, outline=outline, fill=fill, id=id)

# --- Cursor Logic ---
def is_within_element(element: dict, x_check: int, y_check: int) -> bool:
    """Checks if given coordinates are within the bounds of a display element."""
    element_type = element['type']
    
    if element_type == 'text':
        x, y = element['position']
        text = element['text']
        # Use getbbox for text dimensions (replaces deprecated getsize)
        text_bbox = font.getbbox(text) # Returns (left, top, right, bottom) relative to (0,0)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        if x <= x_check <= x + text_width and y <= y_check <= y + text_height:
            return True
    
    elif element_type in ['rectangle', 'ellipse', 'circle']:
        x1, y1, x2, y2 = element['bbox']
        if x1 <= x_check <= x2 and y1 <= y_check <= y2:
            # For ellipses/circles, a more precise check involves the equation of the shape
            # but for a simple bounding box check, this is sufficient.
            # For perfect circle/ellipse check:
            if element_type in ['ellipse', 'circle']:
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                a = abs(x2 - x1) / 2 # horizontal semi-axis
                b = abs(y2 - y1) / 2 # vertical semi-axis
                # Avoid division by zero if semi-axis is 0
                if (a == 0 and x_check != cx) or (b == 0 and y_check != cy):
                    return False
                if (a == 0 or b == 0) or (((x_check - cx)**2) / (a**2) + ((y_check - cy)**2) / (b**2) <= 1):
                    return True
            else: # Rectangle
                return True
    
    return False

def cursor_handler(x_cursor: int | None, y_cursor: int | None, clicked: bool) -> None:
    """
    Handles cursor interaction with display elements.
    If an element is "focused" by the cursor, actions can be triggered,
    especially if 'clicked' is true.
    """
    if x_cursor is None or y_cursor is None:
        return # Cannot handle cursor if coordinates are unknown

    for element in display_elements:
        if is_within_element(element, x_cursor, y_cursor):
            # Element is under the cursor
            # You can add visual feedback here, e.g., changing outline color of the element
            # print(f"Cursor hovering over: {element.get('id', element.get('type'))}") # For debugging

            if clicked:
                element_id = element.get('id')
                print(f"Element clicked: {element_id}") # For debugging
                if element_id == "Off button":
                    global death_flag
                    death_flag = True
                    print("Death flag set. Shutting down...")
                # Add more button actions here:
                # elif element_id == "Some other button":
                #     # Do something
                #     pass

def update_cursor_on_display(x: int, y: int) -> None:
    """
    Updates the position of the visual cursor element on the display.
    Ensures only one cursor is drawn.
    """
    global cursor_coordinates
    cursor_coordinates = (x, y) # Update the global cursor position

    # Find and update the existing cursor element
    cursor_found = False
    for i, element in enumerate(display_elements):
        if element.get('id') == 'main_cursor':
            # Calculate new bbox for the circle
            bbox = (x - cursor_radius, y - cursor_radius, x + cursor_radius, y + cursor_radius)
            display_elements[i]['bbox'] = bbox
            cursor_found = True
            break
    
    if not cursor_found:
        # If cursor element doesn't exist (first run), add it
        add_circle(x, y, cursor_radius, outline="white", id="main_cursor")
    
    redraw_display() # Always redraw after cursor update

def ble_cursor_handler(dx: int, dy: int) -> tuple[int, int]:
    """
    Adjusts cursor coordinates based on BLE delta movements and updates its display.
    Clamps cursor to display boundaries.
    """
    current_x, current_y = cursor_coordinates
    
    new_x = max(0, min(device_width - 1, current_x + dx))
    new_y = max(0, min(device_height - 1, current_y + dy))
    
    update_cursor_on_display(new_x, new_y)
    
    return new_x, new_y

# --- Initializing Sequence ---
def initializing() -> None:
    """Displays an initialization sequence on the OLED."""
    display_clear()
    add_rectangle(device.bounding_box, outline="white", fill="black")
    
    # Centered text
    yorha_text = "YoRHa"
    glory_text = "For the glory\nof Mankind"
    
    # Using getbbox for precise text positioning
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
    """Displays the current time on the top left of the screen."""
    current_time_obj = localtime()
    current_hour = current_time_obj.tm_hour
    current_min = current_time_obj.tm_min
    
    # Format to ensure two digits
    time_str = f"{current_hour:02d}:{current_min:02d}"
    
    add_text((0, 0), time_str, fill="white", id="clock_display")

def death_button() -> None:
    """Adds an 'Off button' to the display."""
    button_text = "OFF" # More intuitive text
    # Position at top-right, accounting for text width
    button_x, button_y = device_width - font.getbbox(button_text)[2] - 5, 5
    add_text((button_x, button_y), button_text, fill="white", id="Off button")

# --- Main GUI Loop Function ---
def GUI_loop_content(x_cursor: int | None, y_cursor: int | None, click: bool) -> None:
    """
    Contains the common GUI display and interaction logic for each frame.
    Called by both camera and BLE modes.
    """
    display_clear() # Always clear the display at the start of a new frame

    death_button()
    clock()

    # Draw the cursor at its current position if it exists
    # We call it here to ensure it's always drawn if input provides coordinates
    if x_cursor is not None and y_cursor is not None:
        update_cursor_on_display(x_cursor, y_cursor)

    # Handle cursor interaction with other elements
    cursor_handler(x_cursor, y_cursor, click)
    
    # Small delay to make updates visible
    sleep(0.1) # Reduced sleep for potentially smoother updates

# --- Main Application Entry Point ---
def main(queue: multiprocessing.Queue | None = None, bl_flag: bool = False, cam_flag: bool = False) -> None:
    """
    Main function to run the OLED display application.
    Handles different input modes (camera or Bluetooth).
    """
    print("Application started.")
    
    if cam_flag:
        print("Running in camera mode.")
        if queue is None:
            print("Error: Camera mode requires a multiprocessing Queue. Exiting.")
            return
    elif bl_flag:
        print("Running in Bluetooth mode.")
    else:
        print("No input mode specified. Please use -bl or -cam. Exiting.")
        return

    # Run the initialization sequence
    initializing()

    # Initialize cursor state for the main loop
    current_x_cursor, current_y_cursor, current_click = cursor_coordinates[0], cursor_coordinates[1], False

    while not death_flag:
        if cam_flag:
            try:
                # Expects (x, y, click) from the camera process via the queue
                # Use a small timeout to keep the loop responsive even without new data
                data = queue.get(timeout=0.05) # Get data from the queue
                current_x_cursor, current_y_cursor, current_click = data
            except multiprocessing.queues.Empty:
                # No new data, just use the last known cursor position and no click
                current_click = False # Assume no click if no new data
                pass
            except Exception as e:
                print(f"Error reading from camera queue: {e}")
                current_x_cursor, current_y_cursor, current_click = None, None, False # Reset on error

        elif bl_flag:
            if not ble_connected_flag:
                ble_connect()
                # If connection fails, wait a bit before retrying to avoid rapid attempts
                if not ble_connected_flag:
                    sleep(2)
                    continue # Skip to next loop iteration if not connected
            
            # Attempt to receive BLE data
            ble_result = ble_receive()
            if ble_result:
                if ble_result[0] == "coor":
                    # Update cursor state if coordinates received
                    current_x_cursor, current_y_cursor, current_click = ble_result[1], ble_result[2], ble_result[3]
                else:
                    # For "notes" or "web", no cursor movement is expected, so reset click
                    current_click = False
            else:
                # No BLE data received, use last known cursor position, and no click
                current_click = False
            
        GUI_loop_content(current_x_cursor, current_y_cursor, current_click)

    print("Application shutdown initiated.")
    # Clean up and display a shutdown message
    display_clear()
    add_text((device_width // 2 - 20, device_height // 2 - 5), "Shutting down...", fill="white")
    sleep(2)
    display_clear()
    # Close BLE client if connected
    if ble_connected_flag and ble_client:
        try:
            Client.close(ble_client)
            print("BLE client closed.")
        except Exception as e:
            print(f"Error closing BLE client: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="OLED Display GUI with external input.")
    parser.add_argument("-bl", "--bluetooth", action="store_true", help="Enable Bluetooth input mode.")
    parser.add_argument("-cam", "--camera", action="store_true", help="Enable Camera input mode (requires a queue).")
    
    args = parser.parse_args()

    # Ensure only one mode is selected
    if args.bluetooth and args.camera:
        print("Error: Please select either Bluetooth (-bl) or Camera (-cam) mode, not both.")
        sys.exit(1)
    if not args.bluetooth and not args.camera:
        print("Error: No input mode specified. Please use -bl or -cam.")
        sys.exit(1)

    # Initialize queue for camera mode if selected
    camera_queue = None
    if args.camera:
        camera_queue = multiprocessing.Queue()
        # IMPORTANT: In a real camera setup, you would start another process here
        # that continuously captures camera input and puts (x, y, click) tuples
        # into the 'camera_queue'. For testing, you might use a dummy feeder process.
        print("Camera mode selected. Ensure a separate process is feeding data to the queue.")

    # Start the main GUI process
    gui_process = multiprocessing.Process(target=main, args=(camera_queue, args.bluetooth, args.camera))
    gui_process.start()
    gui_process.join() # Wait for the GUI process to finish

    print("Application process terminated.")
