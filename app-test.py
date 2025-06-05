import kivy
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.input import MotionEvent
from kivy.uix.widget import Widget
from kivy.clock import mainthread # For updating UI from a non-main thread
from ble_references import Server # Ensure ble_references.py is in the same directory
import requests
import re
from threading import Thread # For running blocking operations in background
import socket # For type hinting

kivy.require('2.1.0')

# Global variables to hold the server and client sockets
# These are kept global for simplicity in this example across Kivy screens.
# For larger apps, consider using Kivy's App class properties for state management.
ble_server_socket: socket.socket | None = None
ble_client_socket: socket.socket | None = None

# This Kivy BooleanProperty will track the Bluetooth connection status.
# It's initially False and will be updated by the connect/disconnect methods.
# It's defined outside the App class but can be accessed via App.get_running_app().is_connected
# This ensures it's a reactive property for Kivy UI elements if needed.
_is_ble_connected = BooleanProperty(False)

# Helper function to send data via BLE
def send_ble_data(data_str: str) -> None:
    """
    Helper function to send a string via BLE.
    It checks if the Bluetooth client socket (from the server's perspective) is active.
    """
    global ble_client_socket, _is_ble_connected
    
    # Get the running app instance to access its properties (like is_connected)
    app = App.get_running_app()

    if not app.is_connected: # Use the app's property for connection status
        # This will be logged by the screen's log method if called from a screen
        print("[ ERROR ] Bluetooth not connected. Cannot send data.")
        return

    if ble_client_socket:
        # Server.send expects the client_socket and the data string
        success = Server.send(ble_client_socket, data_str)
        if success:
            print(f"Data sent: {data_str}")
        else:
            print(f"[ ERROR ] Failed to send data: {data_str}. Connection might be broken.")
            # If send fails, connection might be broken. Update connection status.
            app.is_connected = False # Update the Kivy property
            _is_ble_connected.set(False) # Also update the global BooleanProperty directly
            # Consider auto-reconnect logic here if desired
    else:
        print("[ ERROR ] BLE client socket is None, but connection flag is True. State mismatch.")
        app.is_connected = False
        _is_ble_connected.set(False)


class BaseScreen(Screen):
    """
    A base class for common logging functionality across screens.
    """
    logs = ObjectProperty(None) # To be bound to a Label in KV

    @mainthread # Ensures UI updates happen on Kivy's main thread
    def log(self, message: str) -> None:
        """Appends a message to the logs display, keeping it to a manageable length."""
        if self.logs:
            # Keep only the last 10 lines to prevent log from growing indefinitely
            current_lines = self.logs.text.splitlines()
            if len(current_lines) >= 10:
                self.logs.text = "\n".join(current_lines[-9:]) + "\n"
            self.logs.text += f"{message}\n"
            print(f"UI Log: {message}") # Also print to console for debugging

class MainWindow(BaseScreen):
    name: str = "main" # Screen name for ScreenManager

    def connect_button(self) -> None:
        """
        Attempts to establish a Bluetooth server connection.
        This Kivy app acts as the Bluetooth Server, waiting for the OLED client to connect.
        """
        global ble_server_socket, ble_client_socket, _is_ble_connected

        # Get the running app instance
        app = App.get_running_app()

        if app.is_connected:
            self.log("Bluetooth server already connected.")
            return

        self.log("Attempting to start Bluetooth server...")
        # Server.connect now returns (server_socket, client_socket) or None
        connection_result = Server.connect()

        if connection_result is None:
            self.log("[ ERROR ] Failed to start Bluetooth server. "
                     "Is Bluetooth active? Is the address/channel correct/available?")
            app.is_connected = False # Update Kivy property
            _is_ble_connected.set(False) # Update global BooleanProperty
        else:
            ble_server_socket, ble_client_socket = connection_result
            app.is_connected = True # Update Kivy property
            _is_ble_connected.set(True) # Update global BooleanProperty
            self.log("Bluetooth server started and client connected!")
            # Note: No need to start Server.receive thread here; the OLED is the client,
            # and it will be sending data *to* this Kivy server.

    def disconnect_button(self) -> None:
        """Closes the Bluetooth server connection."""
        global ble_server_socket, ble_client_socket, _is_ble_connected

        # Get the running app instance
        app = App.get_running_app()

        if not app.is_connected:
            self.log("Bluetooth server not active or already disconnected.")
            return

        self.log("Closing Bluetooth server...")
        try:
            # Server.close handles closing both sockets
            Server.close(ble_server_socket, ble_client_socket)
            self.log("Bluetooth server closed.")
        except Exception as e:
            self.log(f"[ ERROR ] Error closing server: {e}")
        finally:
            ble_server_socket = None
            ble_client_socket = None
            app.is_connected = False # Update Kivy property
            _is_ble_connected.set(False) # Update global BooleanProperty


class SecondWindow(BaseScreen):
    name: str = "second"
    notes = ObjectProperty(None) # For the TextInput

    def send_notes(self) -> None:
        """Sends the text from the notes TextInput via BLE."""
        note_text = self.notes.text.strip()
        if not note_text:
            self.log("Note cannot be empty.")
            return

        # Format data as "notes,your_text" as expected by the OLED GUI client
        data_to_send = f"notes,{note_text}"
        send_ble_data(data_to_send)
        self.log("Note data sent (if connected).")
        self.notes.text = "" # Clear input after sending


class ThirdWindow(BaseScreen):
    name: str = "third"
    query = ObjectProperty(None) # For the TextInput

    def _perform_web_search_and_send(self, query_text: str) -> None:
        """
        Private method to perform the web search and send the result.
        This runs in a background thread.
        """
        try:
            # Replace spaces with '+' for URL encoding
            computed_query = re.sub(r'[ ]+', '+', query_text)
            search_url = f"https://duckduckgo.com/?q={computed_query}&ia=web"
            self.log(f"Searching: {search_url}")

            # Perform HTTP GET request with a timeout
            response = requests.get(search_url, timeout=5)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            page_source = response.text

            # Simple extraction: try to find a meaningful text snippet
            # This regex attempts to find the first paragraph that isn't just whitespace
            # or a very short, common element. This is a heuristic and might need tuning.
            match = re.search(r'<p[^>]*>(?!<img.*?>)\s*(.+?)\s*</p>', page_source, re.DOTALL | re.IGNORECASE)
            summary = "No relevant text found."
            if match:
                # Clean up HTML tags and multiple spaces from the extracted text
                raw_text = match.group(1)
                summary = re.sub(r'<[^>]*>', '', raw_text) # Remove HTML tags
                summary = re.sub(r'\s+', ' ', summary).strip() # Replace multiple spaces with single space

            # Limit summary length for OLED display (e.g., 50 characters + ellipsis)
            summary = summary[:50] + "..." if len(summary) > 50 else summary

            # Format data as "web,your_summary" as expected by the OLED GUI client
            data_to_send = f"web,{summary}"
            send_ble_data(data_to_send)
            self.log("Web search result sent (if connected).")

        except requests.exceptions.RequestException as e:
            self.log(f"[ ERROR ] Web search failed: Network or HTTP error: {e}")
        except Exception as e:
            self.log(f"[ ERROR ] Unexpected error during web search: {e}")

    def web_search_button(self) -> None:
        """
        Triggers a web search in a new thread and sends the result via BLE.
        Prevents UI from freezing.
        """
        query_text = self.query.text.strip()
        if not query_text:
            self.log("Search query cannot be empty.")
            return

        self.log("Starting web search...")
        # Run the search in a separate thread to avoid blocking the UI
        Thread(target=self._perform_web_search_and_send, args=(query_text,), daemon=True).start()
        self.query.text = "" # Clear input after triggering search


class TouchPad(Widget):
    """
    A custom Kivy Widget that functions as a touchpad, detecting touch movements
    and sending corresponding BLE messages.
    """
    # Kivy properties to store previous touch coordinates for calculating delta
    prev_x = ObjectProperty(0)
    prev_y = ObjectProperty(0)
    # Boolean property to track if a touch is currently active on the touchpad
    is_touching = BooleanProperty(False)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        """Handles when a touch starts on the touchpad."""
        # Check if the touch event occurred within this widget's boundaries
        if self.collide_point(*touch.pos):
            self.is_touching = True
            # Store initial touch position for calculating deltas on move
            self.prev_x, self.prev_y = touch.x, touch.y
            
            # Send initial click state as 'true' for a touch-down event
            # dx and dy are 0 as there's no movement on the initial press
            data_to_send = f"d_coordinates,0,0,true"
            send_ble_data(data_to_send)
            return True # Consume the event so other widgets don't handle it
        return False

    def on_touch_move(self, touch: MotionEvent) -> bool:
        """Handles when a touch moves across the touchpad."""
        # Only process move events if a touch is active and within widget bounds
        if self.is_touching and self.collide_point(*touch.pos):
            # Calculate the change in X and Y coordinates
            dx = int(touch.x - self.prev_x)
            dy = int(touch.y - self.prev_y) # Kivy y-axis is inverted from OLED's typical, but OLED handles relative motion.

            # Only send data if there's significant movement to avoid spamming BLE
            # Adjust the threshold (e.g., 1) as needed for sensitivity
            if abs(dx) > 0 or abs(dy) > 0:
                # Send movement data with click state as 'false' (it's a move, not a discrete click)
                data_to_send = f"d_coordinates,{dx},{dy},false"
                send_ble_data(data_to_send)
                # print(f"Sent movement: {data_to_send}") # For debugging

            # Update previous position for the next movement calculation
            self.prev_x, self.prev_y = touch.x, touch.y
            return True # Consume the event
        return False

    def on_touch_up(self, touch: MotionEvent) -> bool:
        """Handles when a touch is released from the touchpad."""
        # Only process if a touch was previously active
        if self.is_touching:
            self.is_touching = False
            # Send click state as 'false' for touch-up (no movement, just release)
            data_to_send = f"d_coordinates,0,0,false"
            send_ble_data(data_to_send)
            # print(f"Sent touch up: {data_to_send}") # For debugging
            return True # Consume the event
        return False


class FourthWindow(BaseScreen):
    name: str = "fourth"
    touchpad = ObjectProperty(None) # This will be bound to the TouchPad instance in KV

    def on_enter(self) -> None:
        """Called when this screen becomes the active screen."""
        self.log("Touchpad screen active. Use the gray area to control the cursor.")
        app = App.get_running_app()
        if not app.is_connected:
            self.log("[ WARNING ] Bluetooth not connected. Touchpad will not send data.")


class WindowManager(ScreenManager):
    """
    Manages the different screens in the application.
    """
    pass


# Load the Kivy Language file.
# This assumes 'ARGlasses.kv' is in the same directory as this Python script.
kv = Builder.load_file("ARGlasses.kv")


class ARGlassesApp(App):
    """
    The main Kivy application class.
    """
    # Make the connection status available to all parts of the app via `app.is_connected`
    is_connected = _is_ble_connected # Bind the global BooleanProperty to an App property

    def build(self):
        """Builds the root widget of the application from the KV file."""
        return kv

    def on_stop(self):
        """
        Called when the app is about to shut down.
        Ensures Bluetooth server sockets are closed cleanly.
        """
        global ble_server_socket, ble_client_socket
        # Use the app's connection status
        if self.is_connected:
            print("App stopping: Closing Bluetooth server...")
            try:
                Server.close(ble_server_socket, ble_client_socket)
            except Exception as e:
                print(f"Error during app shutdown closing BLE: {e}")
            finally:
                # Ensure sockets are set to None even if closing failed
                ble_server_socket = None
                ble_client_socket = None


if __name__ == '__main__':
    ARGlassesApp().run()
