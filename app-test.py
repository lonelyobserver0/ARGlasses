import kivy
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.pagelayout import PageLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from kivy.input import MotionEvent
from kivy.graphics import Line
from queue import Queue
from threading import Thread
from ble_references import Server
import requests
import re

kivy.require('2.1.0')

q = Queue()
server, client = None, None
t1 = Thread(target=Server.receive, args=(client, q), daemon=True)
ble_flag = 1


class MainWindow(Screen):

    logs = ObjectProperty(None)

    i = 0

    def log(self, log):

        if self.i == 1:
            self.logs.text = ""
            self.i = 0

        self.logs.text = log

        self.i += 1

    def connect_button(self):

        global server, client
        server, client = Server.connect()

        if server == 1 and client == 1:

            print("[ ERROR 00148 ] Inactive network detected during socket execution. Activate Bluetooth before trying again.")
            self.log("[ ERROR 00148 ] Inactive network detected during socket execution. Activate Bluetooth before trying again.")

            global ble_flag
            ble_flag = 1

        else:

            print("Starting server")
            self.log("Starting server")

            t1.start()

            print("Server started")
            self.log("Server started")
            
            ble_flag = 0


    def disconnect_button(self):

        global server, client

        print("Closing server")
        self.log("Closing server")
        try:

            t1.join()

            Server.close(server, client)

            print("Closed server")
            self.log("Closed server")

        except RuntimeError:

            print("[ ERROR 00149 ] Server already closed")
            self.log("[ ERROR 00149 ] Server already closed")


class SecondWindow(Screen):

    notes = ObjectProperty(None)
    logs = ObjectProperty(None)

    i = 0

    def log(self, log):

        if self.i == 1:
            self.logs.text = ""
            self.i = 0

        self.logs.text = log

        self.i += 1


    def send_notes(self):

        notes = ["notes", self.notes.text]
        print(notes)

        if not notes:
            pass
        
        else:

            if ble_flag == 1:
                print("[ ERROR 00150 ] Bluetooth daemon not started")
                self.log("[ ERROR 00150 ] Bluetooth daemon not started")

            else:
                Server.send(client, notes)
                self.log("Data was sent")


class ThirdWindow(Screen):

    query = ObjectProperty(None)
    logs = ObjectProperty(None)

    i = 0

    def log(self, log):

        if self.i == 1:
            self.logs.text = ""
            self.i = 0

        self.logs.text = log

        self.i += 1


    def web_search(self):

        query = self.query.text

        if not query:
            pass
        else:
            computed_query = re.sub(r'[ ]', '+', query)
            search_query = f"https://duckduckgo.com/?q={computed_query}&ia=web"
            response = requests.get(search_query)
            page_source = response.text


class TouchPad(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_touching = False


    def on_touch_move(self, touch):
        if self.is_touching:
            dx = touch.x - self.prev_x
            dy = touch.y - self.prev_y

            data = ("d_coordinates", dx, dy)
            if ble_flag == 1:
                print("[ ERROR 00150 ] Bluetooth daemon not started")

            else:
                Server.send(client, data)
                print("Data was sent")
            print(data)
            print("---------------------------")

            self.prev_x, self.prev_y = touch.x, touch.y


    def on_touch_down(self, touch):
        self.is_touching = True
        self.prev_x, self.prev_y = touch.x, touch.y
        return super().on_touch_down(touch)


    def on_touch_up(self, touch):
        self.is_touching = False
        return super().on_touch_up(touch)


class FourthWindow(Screen):

    logs = ObjectProperty(None)

    i = 0

    def log(self, log):

        if self.i == 1:
            self.logs.text = ""
            self.i = 0

        self.logs.text = log

        self.i += 1


    def on_enter(self):
            self.touchpad.bind(on_touch_move=self.on_touchpad_move)


    def on_touchpad_move(self, instance, touch):

        """
        x_ratio, y_ratio = 128 / self.touchpad.size[0], 64 / self.touchpad.size[1]
        x_real, y_real = int(touch.pos[0] * x_ratio), int(64-(touch.pos[1] * y_ratio))

        data = f"cursor_coordinates-->{x_real}, {y_real}"
        print(data)

        if ble_flag == 1:
                # print("[ ERROR 00150 ] Bluetooth daemon not started")
                self.log("[ ERROR 00150 ] Bluetooth daemon not started")

        else:
            Server.send(client, data)
            self.log("Data was sent")
        """

        pass


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file("ARGlasses.kv")


class ARGlassesApp(App):
    def build(self):
        return kv


if __name__ == '__main__':
    ARGlassesApp().run()
