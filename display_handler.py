from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont, ImageDraw # Import ImageDraw for text bounding box calculation
from time import sleep, localtime
from ble_references import Client # Assuming ble_references and Client are correctly defined
import sys
import multiprocessing

# --- Configuration Constants ---
# Font and Display
FONT_PATH = "NixieOne.ttf"
DEFAULT_FONT_SIZE = 10 # Changed from 1 to a more readable size
SPLASH_FONT_SIZE = 16

# Cursor
CURSOR_RADIUS_FACTOR = 4 # Cursor radius will be device_min_dim / CURSOR_RADIUS_FACTOR
BLE_RECONNECT_DELAY_SEC = 2 # Delay before retrying BLE connection

# UI Element IDs
OFF_BUTTON_ID = "Off button"
# Add other UI element IDs here if needed

# --- Global Variables ---
# Initializing flags from command line arguments
BLE_ENABLED, CAM_ENABLED = False, False
for arg in sys.argv:
    if arg == "-bl":
        BLE_ENABLED = True
    elif arg == "-cam":
        CAM_ENABLED = True

# Display setup
serial = spi(device=0, port=0)
device = ssd1309(serial)
DEVICE_WIDTH = device.width
DEVICE_HEIGHT = device.height
MIN_DEVICE_DIM = min(DEVICE_WIDTH, DEVICE_HEIGHT)

# Load font (ensure NixieOne.ttf is in the same directory or provide full path)
try:
    font = ImageFont.truetype(FONT_PATH, DEFAULT_FONT_SIZE)
    splash_font = ImageFont.truetype(FONT_PATH, SPLASH_FONT_SIZE)
except IOError:
    print(f"Error: Font file '{FONT_PATH}' not found. Using default font.")
    font = ImageFont.load_default()
    splash_font = ImageFont.load_default()

display_elements = [] # List to hold elements to be drawn on the next frame

cursor_coordinates = (0, 0)
cursor_radius = MIN_DEVICE_DIM // CURSOR_RADIUS_FACTOR

death_flag = multiprocessing.Value('b', False) # Using multiprocessing.Value for shared flag

ble_client = None
ble_connected = False

# --- BLE Functions ---
def ble_connect():
    """Attempts to connect to the BLE client."""
    global ble_client, ble_connected
    try:
        ble_client = Client.connect()
        ble_connected = True
        print("BLE client connected.")
    except Exception as e:
        ble_connected = False
        print(f"BLE connection failed: {e}")

def ble_receive():
    """Receives data from the BLE client and processes it."""
    if not ble_connected or ble_client is None:
        return None

    try:
        data = Client.receive(ble_client)
        if data is None: # No data received
            return None

        print(f"Received BLE data: {data}")
        if data[0] == "notes":
            # Example: display notes
            # For this example, we'll just print it, or you can add a temporary UI element
            # add_text((10, 10), f"Note: {data[1]}", fill="white")
            pass
        elif data[0] == "web":
            # Example: display web data
            # add_text((10, 30), f"Web: {data[1]}", fill="white")
            pass
        elif data[0] == "d_coordinates":
            # Returns data for cursor movement
            return ("cursor_move", data[1], data[2], data[3]) # dx, dy, click
        return None # Return None if data is not for cursor movement
    except Exception as e:
        print(f"Error receiving BLE data: {e}")
        # Consider setting ble_connected = False here if error indicates disconnection
        return None

# --- Display Management Functions ---
def add_element(element_type, **kwargs):
    """Adds a generic element to the display_elements list."""
    # Ensure a font is always provided for text elements
    if element_type == 'text' and 'font_override' in kwargs:
        kwargs['font'] = kwargs.pop('font_override') # Rename for consistency
    elif element_type == 'text' and 'font' not in kwargs:
        kwargs['font'] = font # Default font for text elements

    display_elements.append({'type': element_type, **kwargs})

def redraw_display():
    """Draws all elements currently in display_elements to the OLED."""
    with canvas(device) as draw:
        for element in display_elements:
            if element['type'] == 'rectangle':
                draw.rectangle(element['bbox'], outline=element['outline'], fill=element['fill'])
            elif element['type'] == 'text':
                draw.text(element['position'], element['text'], fill=element['fill'], font=element['font'])
            elif element['type'] == 'ellipse':
                draw.ellipse(element['bbox'], outline=element['outline'], fill=element['fill'])

def display_clear():
    """Clears the display and the list of elements."""
    global display_elements
    device.clear()
    display_elements = []

# --- UI Element Specific Add Functions ---
def add_rectangle(bbox, outline="white", fill="black", id=None):
    add_element('rectangle', bbox=bbox, outline=outline, fill=fill, id=id)

def add_text(position, text, fill="white", id=None, font_override=None):
    add_element('text', position=position, text=text, fill=fill, id=id, font_override=font_override)

def add_ellipse(bbox, outline="white", fill="black", id=None):
    add_element('ellipse', bbox=bbox, outline=outline, fill=fill, id=id)

def add_circle(center_x, center_y, radius, outline="white", fill="black", id=None):
    """Adds a circle element to the display_elements list."""
    # Convert center_x, center_y, radius to bounding box for ellipse drawing
    bbox = (center_x - radius, center_y - radius, center_x + radius, center_y + radius)
    add_element('ellipse', bbox=bbox, outline=outline, fill=fill, id=id)

# --- Cursor and Interaction ---
def is_within_element(element, x_check, y_check):
    """Checks if a given coordinate (x_check, y_check) is within an element."""
    element_type = element['type']

    if element_type == 'text':
        x, y = element['position']
        text = element['text']
        element_font = element.get('font', font)
        # Use getbbox() for accurate text size
        try:
            bbox = element_font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError: # Fallback for older Pillow or default fonts without getbbox
            text_width, text_height = element_font.getsize(text)

        if x <= x_check <= x + text_width and y <= y_check <= y + text_height:
            return True

    elif element_type in ['rectangle', 'ellipse']: # Both use bbox (x1, y1, x2, y2)
        x1, y1, x2, y2 = element['bbox']
        # For ellipse, true hit test is more complex, but for simple UI, AABB check is often sufficient
        if x1 <= x_check <= x2 and y1 <= y_check <= y2:
            return True

    return False

def handle_cursor_click(clicked_x, clicked_y):
    """Handles a click event at the given coordinates."""
    global death_flag
    for element in display_elements:
        if element.get('id') and is_within_element(element, clicked_x, clicked_y):
            print(f"Element '{element['id']}' clicked at ({clicked_x}, {clicked_y})")
            if element['id'] == OFF_BUTTON_ID:
                death_flag.value = True # Set shared flag
                print("Off button clicked. Setting death_flag.")
            # Add more specific click handlers for other UI elements here
            # elif element['id'] == "Some other button":
            #     perform_action_for_some_other_button()
            return True # Element was clicked
    return False # No element was clicked

def update_cursor_position(dx, dy):
    """Updates the global cursor coordinates based on deltas."""
    global cursor_coordinates
    new_x = max(0, min(DEVICE_WIDTH - 1, cursor_coordinates[0] + dx))
    new_y = max(0, min(DEVICE_HEIGHT - 1, cursor_coordinates[1] + dy))
    cursor_coordinates = (new_x, new_y)
    return cursor_coordinates

# --- UI Specific Functions ---
def initializing_screen():
    """Displays an initialization sequence on the OLED."""
    display_clear()
    add_rectangle((0, 0, DEVICE_WIDTH - 1, DEVICE_HEIGHT - 1), outline="white", fill="black")
    add_text((DEVICE_WIDTH / 2 - 20, DEVICE_HEIGHT / 2 - 15), "YoRHa", fill="white", font_override=splash_font)
    add_text((DEVICE_WIDTH / 2 - 40, DEVICE_HEIGHT / 2 + 5), "For the glory\nof Mankind", fill="white", font_override=font)
    redraw_display()
    sleep(4)

    display_clear()
    add_text((0, 0), "Initializing...", fill="white")
    redraw_display()
    sleep(2)

    add_text((0, 20), "Checking filesystem\nintegrity... OK", fill="white")
    redraw_display()
    sleep(2)

    display_clear()
    add_text((0, 0), "Interlink status... OK", fill="white")
    redraw_display()
    sleep(2)

    add_text((0, 20), "Primary function\nstatus... OK", fill="white")
    redraw_display()
    sleep(2)

    display_clear()
    add_text((0, 0), "Connections status... OK", fill="white")
    redraw_display()
    sleep(2)

    display_clear() # Clear before main UI starts

def draw_clock():
    """Adds the current time to the display elements."""
    current_time = localtime()
    hour = str(current_time.tm_hour).zfill(2)
    minute = str(current_time.tm_min).zfill(2)
    # second = str(current_time.tm_sec).zfill(2) # If you want seconds
    time_str = f"{hour}:{minute}" # :{second}"
    add_text((0, 0), time_str, fill="white")

def draw_death_button():
    """Adds the 'CTB' (Click To B...) button to the display elements."""
    button_text = "CTB"
    # Calculate text dimensions to center the button or size a rectangle around it
    text_bbox = font.getbbox(button_text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    button_x = 5
    button_y = 5
    button_padding = 2 # Padding around the text
    button_rect_bbox = (button_x, button_y, button_x + text_width + 2 * button_padding, button_y + text_height + 2 * button_padding)

    add_rectangle(button_rect_bbox, outline="white", id=OFF_BUTTON_ID)
    add_text((button_x + button_padding, button_y + button_padding), button_text, fill="white", id=OFF_BUTTON_ID)


def draw_cursor():
    """Draws the cursor circle at its current coordinates."""
    add_circle(cursor_coordinates[0], cursor_coordinates[1], cursor_radius, outline="white")

# --- Main UI Rendering Loop ---
def update_gui(current_x, current_y, clicked):
    """
    Renders the current state of the GUI.
    This function should be called repeatedly to update the display.
    """
    display_clear() # Clear elements from previous frame

    # Add all persistent UI elements
    draw_death_button()
    draw_clock()

    # Draw the cursor based on its current position
    draw_cursor()

    # Handle interactions (after elements are drawn so is_within_element works)
    if clicked:
        handle_cursor_click(current_x, current_y)

    redraw_display() # Draw everything to the OLED for the current frame

# --- Main Execution ---
def main(queue):
    """Main function to manage display and input."""
    print(f"Starting with BLE_ENABLED: {BLE_ENABLED}, CAM_ENABLED: {CAM_ENABLED}")

    if not BLE_ENABLED and not CAM_ENABLED:
        print("Warning: No input mode selected. Please use -bl or -cam.")
        # Default to a mode or exit if no input is acceptable
        # For now, let's assume it should run without specific input if no flags are given
        # or you might want to sys.exit() here.

    initializing_screen()

    # Set initial cursor position
    global cursor_coordinates
    cursor_coordinates = (DEVICE_WIDTH // 2, DEVICE_HEIGHT // 2)

    while not death_flag.value: # Loop until the shared death_flag is set
        current_x, current_y = cursor_coordinates
        click_event = False

        if CAM_ENABLED:
            # Check for camera input from the queue
            if not queue.empty():
                try:
                    data = queue.get_nowait() # Get data without blocking
                    if len(data) == 3: # Expecting (x, y, click)
                        current_x, current_y, click_event = data
                        # Clamp camera coordinates to display bounds
                        current_x = max(0, min(DEVICE_WIDTH - 1, current_x))
                        current_y = max(0, min(DEVICE_HEIGHT - 1, current_y))
                        cursor_coordinates = (current_x, current_y) # Update global cursor pos
                    else:
                        print(f"Warning: Unexpected data format from camera queue: {data}")
                except multiprocessing.Queue.Empty:
                    pass # Queue was empty, just continue

        elif BLE_ENABLED:
            if not ble_connected:
                ble_connect()
                if not ble_connected:
                    # If connection failed, wait and try again
                    sleep(BLE_RECONNECT_DELAY_SEC)
                    continue # Skip to next loop iteration to retry connection
            else:
                ble_data = ble_receive()
                if ble_data and ble_data[0] == "cursor_move":
                    dx, dy, click = ble_data[1], ble_data[2], ble_data[3]
                    update_cursor_position(dx, dy)
                    click_event = click
                # Other BLE data types (notes, web) handled within ble_receive() implicitly
                # but you could add specific UI updates here if needed, e.g., temporary pop-ups.

        # Update the GUI based on the current cursor state and click
        update_gui(current_x, current_y, click_event)

        sleep(0.05) # Small delay to reduce CPU usage and control frame rate

    print("Main loop finished. Shutting down.")
    # Clean up BLE connection if active
    if ble_connected and ble_client:
        try:
            Client.disconnect(ble_client)
            print("BLE client disconnected successfully.")
        except Exception as e:
            print(f"Error during BLE client disconnect: {e}")

# --- Entry Point ---
if __name__ == "__main__":
    # Create a multiprocessing Queue for inter-process communication (e.g., camera input)
    input_queue = multiprocessing.Queue()

    # Start the main UI process
    ui_process = multiprocessing.Process(target=main, args=(input_queue,))
    ui_process.start()

    # Example: If you had a camera process, it would put data into input_queue here
    # For demonstration, let's simulate some camera input if CAM_ENABLED is True
    if CAM_ENABLED:
        print("Simulating camera input for demonstration...")
        # Simulate some clicks and moves
        for _ in range(5):
            input_queue.put((DEVICE_WIDTH // 4, DEVICE_HEIGHT // 4, True)) # Click top-left
            sleep(0.5)
            input_queue.put((DEVICE_WIDTH // 2, DEVICE_HEIGHT // 2, False)) # Move to center
            sleep(0.5)
            input_queue.put((DEVICE_WIDTH * 3 // 4, DEVICE_HEIGHT * 3 // 4, False)) # Move to bottom-right
            sleep(0.5)
            input_queue.put((DEVICE_WIDTH // 2, DEVICE_HEIGHT // 2, True)) # Click center

        # Simulate clicking the "Off button"
        # The actual coordinates depend on where you draw your "CTB" button
        # Based on draw_death_button: (5, 5) for text, so a click around there
        input_queue.put((10, 10, True)) # Simulate a click on the CTB button
        print("Simulated camera input finished.")


    # Wait for the UI process to finish (when death_flag is set)
    ui_process.join()
    print("Program terminated.")
    