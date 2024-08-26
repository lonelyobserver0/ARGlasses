import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from ble_references import Server
from queue import Queue
from threading import Thread

kivy.require('2.1.0')
Window.clearcolor = (55/255, 147/255, 222/255, 0/255)

q = Queue()
server, client = None, None
t1 = Thread(target=Server.receive, args=(client, q), daemon=True)


class HomeScreen(GridLayout):

    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.cols = 1
        self.rows = 12

        print("Execution so divine")

        self.add_widget(Label(text='Insert notes to keep on show'))
        self.userNoteInput = TextInput(multiline=True)
        self.userNoteInput.size_hint = (1, 2)
        self.add_widget(self.userNoteInput)

        self.button1 = Button(text="Send notes")
        self.button1.bind(on_press=self.pressed1)
        self.add_widget(self.button1)

        self.button1_2 = Button(text="")
        self.add_widget(self.button1_2)

        self.button2 = Button(text="Button 2")
        self.button2.bind(on_press=self.pressed2)
        self.add_widget(self.button2)

        self.button3 = Button(text="Refresh")
        self.button3.bind(on_press=self.pressed3)
        self.add_widget(self.button3)

        self.btn4 = False
        self.btn4_1 = False
        self.button4 = Button(text="Click to connect to bluetooth", background_color=[0.796, 0, 0, 1])
        self.button4.bind(on_press=self.pressed4)
        self.add_widget(self.button4)

    def pressed1(self, instance):
        message = self.userNoteInput.text
        print(message)
        message = "notes"+message
        Server.send(client, message)

    # If method does not use self parameter
    @staticmethod
    def pressed2(self):
        print("BUTTON 2")

    @staticmethod
    def pressed3(self, instance):
        print(q)

    def pressed4(self, instance):
        if not self.btn4:
            print("Start server")
            global server, client
            server, client = Server.connect()

            if not self.btn4_1:
                t1.start()
                self.btn4_1 = True

            self.button4.text = "Click to close server"
            self.btn4 = True
        else:
            t1.join()
            Server.close(server, client)
            self.btn4 = False


class SmartGlassesApp(App):
    def build(self):
        return HomeScreen()


if __name__ == '__main__':
    SmartGlassesApp().run()
