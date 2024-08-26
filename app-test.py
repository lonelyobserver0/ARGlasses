import kivy
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.pagelayout import PageLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from queue import Queue
from threading import Thread
from ble_references import Server

kivy.require('2.1.0')

q = Queue()
server, client = None, None
t1 = Thread(target=Server.receive, args=(client, q), daemon=True)
ble_flag = 0


class MainWindow(Screen):

    def connect_button(i):

        global server, client
        server, client = Server.connect()

        if server == 1 and client == 1:

            print("[ERROR 00148] Inactive network detected during socket execution. Activate Bluetooth before trying again.")
            global ble_flag
            ble_flag = 1

        else:

            print("Starting server")
            t1.start()
            print("Started server")

    def disconnect_button():

        print("Closing server")
        t1.join()
        Server.close(server, client)
        print("Closed server")


class SecondWindow(Screen):

    notes = ObjectProperty(None)

    def send_notes(self):

        notes = self.notes.text

        if not notes:
            pass
        
        else:

            if ble_flag == 1:
                pass

            else:
                Server.send(client, notes)


class ThirdWindow(Screen):

    search_query = ObjectProperty(None)

    def web_search(self):

        query = self.search_query.text

        if not query:
            pass
        else:
            print(query)
            # Search and display the content of the URL (query)


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file("ARGlasses.kv")


class ARGlassesApp(App):
    def build(self):
        return kv


if __name__ == '__main__':
    ARGlassesApp().run()
