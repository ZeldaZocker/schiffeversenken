from logging import root
import sys
from tkinter.ttk import Labelframe

print("Running Python version: " + str(sys.version))
from base64 import encode
import socket
from threading import Thread
import json
import time
import signal

from network import NetworkClient
from network import MessageID

from tkinter import *
from tkinter import messagebox

class GameWindow(Thread):
    is_destroyed = False
    DEFAULT_BG = "#404040"

    def __init__(self, client):
        Thread.__init__(self)
        self.client = client
    
    def run(self):
        self.root = Tk()
        self.root.title("Schiffe Versenken von Noah")
        self.root.geometry("620x680")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.configure(bg=self.DEFAULT_BG)

        Frame(self.root, width=70, height=60, highlightbackground="yellow", highlightthickness=4, bg=self.DEFAULT_BG).grid(row=0, column=0, rowspan=2)

        self.button_frame = Frame(self.root, width=60*8, height=40, highlightbackground="red", highlightthickness=2, bg=self.DEFAULT_BG)
        self.button_frame.grid(row=0, column=1)
        self.button_frame.grid_propagate(False)
        
        self.button_frame.columnconfigure(0, weight=1, pad=30)
        self.button_frame.rowconfigure(0,weight=1, pad=30)

        text_frame = Frame(self.root, width=60*8, height=20, bg=self.DEFAULT_BG)
        text_frame.grid(row=1, column=1)
        text_frame.grid_propagate(False)
        
        text_frame.columnconfigure(0, weight=1, pad=30)
        text_frame.rowconfigure(0,weight=1, pad=30)

        self.text = Label(text_frame, text="You're not supposed to see this!",fg="red", bg=self.DEFAULT_BG)
               
        Frame(self.root, width=70, height=60, highlightbackground="yellow", highlightthickness=4, bg=self.DEFAULT_BG).grid(row=0, column=2, rowspan=2)

        
        btnString = StringVar(self.button_frame, "Join Server")
        self.join_server_button = Button(self.button_frame, bg="gray", textvariable=btnString, command=self.join_server_btn)
        self.join_server_button.grid(sticky="wens")
        self.join_server_button.grid_remove()

        btnString = StringVar(self.button_frame, "Join Queue")
        self.join_queue_button = Button(self.button_frame, bg="gray", textvariable=btnString, command=self.join_queue_btn)
        self.join_queue_button.grid(sticky="wens")
        self.join_queue_button.grid_remove()

        btnString = StringVar(self.button_frame, "Leave Queue")
        self.leave_queue_button = Button(self.button_frame, bg="gray", textvariable=btnString, command=self.leave_queue_btn)
        self.leave_queue_button.grid(sticky="wens")
        self.leave_queue_button.grid_remove()

        self.join_server_button.grid()

        
        

        button_list = []
        z = 0
        self.board_frame = Frame(self.root, width=630, height=630, highlightbackground="red", highlightthickness=2)
        self.board_frame.grid_propagate(False)
        self.board_frame.grid(row=1, column=1, padx=0, pady=0)

        for y in range(10):
            for x in range(10):
                btnString = StringVar(self.board_frame, f"{x} {y}")
                frame = Frame(self.board_frame, width=60, height=60, highlightbackground="blue", highlightthickness=2)
                frame.grid_propagate(False)
                frame.columnconfigure(0, weight=1, pad=30)
                frame.rowconfigure(0,weight=1, pad=30)
                frame.grid(row=y, column=x, padx=1, pady=1)

                cmd = lambda x=x, y=y: client.shoot(x,y)
                print(x,y)
                btn = Button(frame, bg="#33ccff", textvariable=btnString, command=cmd)
                btn.grid(sticky="wens")
                #btn.grid(row=i, column=z)
                button_list.append(btn)
        self.board_frame.grid_remove()

        self.root.mainloop()

    def join_server_btn(self):
        if not self.client.connect_to_master():
            self.text.config(text="Error connecting to server!", fg="red")
            self.text.pack()
            return
        thr = Thread(target=self.client.handle_message, args=())
        thr.start()
        self.join_server_button.grid_remove()
        self.join_queue_button.grid()
        
    def join_queue_btn(self):
        self.client.join_queue()
        self.join_queue_button.grid_remove()
        self.leave_queue_button.grid()

    def leave_queue_btn(self):
        pass

    def quit(self):
        self.root.quit()
        self.is_destroyed = True
        self.client.is_running = False


class Client():

    PREFIX = "[CLIENT]"
    is_running = False
    joined_queue = False
    game_window = None

    def start(self):
        self.is_running = True
        while self.is_running:
            time.sleep(1)

    def connect_to_master(self):
        self.network_client = NetworkClient(socket.gethostname(), 20550)
        self.network_client.connect()
        if not self.network_client.is_connected:
            print(f"{self.PREFIX} Error connecting to master server. (Step 1)")
            return False
        message = self.network_client.recv()
        if not message.get('action') == MessageID.OK.value:
            print(f"{self.PREFIX} Error connecting to master server. (Step 2)")
            self.purge_client()
            return False
        self.network_client.client_id = message.get('payload')
        print(self.PREFIX, self.network_client.client_id)
        print(f"{self.PREFIX} Server accepted connection.")
        return True

    def join_queue(self):
        self.network_client.send(MessageID.ADD_QUEUE.value)
        joined_queue_time = time.time()
        while not self.joined_queue:
            if time.time() - joined_queue_time > 10:
                print(f"{self.PREFIX} Error joining queue.")
                return False
        print(f"{self.PREFIX} Joined queue.")
        return True

    def ping(self):
        self.network_client.send(MessageID.PING.value)

    def wait_for_message(self):
        return self.network_client.recv()

    def join_game_server(self, msg):
        print("{self.PREFIX} FINALLY!!")
        print(f"{self.PREFIX} payload: {msg.get('payload')}")
        self.network_client.send(MessageID.DISCONNECT.value, client_id=self.network_client.client_id)
        self.network_client.client.close()
        self.network_client = NetworkClient(msg.get('payload')[0], msg.get('payload')[1])
        self.network_client.connect()
        msg = self.network_client.recv()
        if not msg.get("action") == MessageID.OK.value:
            self.handle_failure("Error while joining game server.")
        self.network_client.client_id = msg.get('payload')

    def handle_message(self):
        try:
            while self.network_client.is_connected and self.is_running:
                msg = self.network_client.recv()
                if not msg:
                    print(f"{self.PREFIX} Server gone?")
                    self.network_client.client.close()
                    return
                print(f"{self.PREFIX} \"{MessageID(msg.get('action'))}\" received!")
                match msg.get("action"):
                    case MessageID.PING.value:
                        self.network_client.last_ping = time.time()
                        self.network_client.send(MessageID.PING.value)
                        print(f"{self.PREFIX} Pong {self.network_client.client_id}")
                    case MessageID.GAMESERVER.value:
                        self.join_game_server(msg)
                        break
                    case MessageID.ADD_QUEUE.value:
                        self.joined_queue = True
                    case MessageID.EMPTY.value:
                            print(f"{self.PREFIX} Empty package case.")
                            self.handle_failure("Server gone. Purging.")
                    case _:
                        print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")
                if self.network_client.last_ping + 10 < time.time():
                    self.network_client.send(MessageID.PING.value)
                time.sleep(0.1)
        except socket.error:
            print(f"{self.PREFIX} Server gone?.")
            self.purge_client()


    def handle_failure(self, message="Received unexpected network package."):
        self.purge_client()
        self.network_client.is_connected = False
        self.is_running = False
        if not self.game_window.is_destroyed:
            self.game_window.quit()
        print(self.PREFIX, message)
        input(f"{self.PREFIX} Press Enter to exit.")
        sys.exit()

    def purge_client(self):
        try:
            self.network_client.send(MessageID.DISCONNECT)
        except:
            pass
        try:
            self.network_client.client.close()
        except:
            pass

    def signal_handler(self, sig, frame):
        print(f"{self.PREFIX} You pressed Ctrl+C!")
        self.is_running = False
        self.purge_client()
        self.game_window.quit()
        sys.exit(0)

    def shoot(self, x, y):
        print(f"Shooting: {x} {y}")

    


if __name__ == '__main__':
    client = Client()
    signal.signal(signal.SIGINT, client.signal_handler)
    game_window = GameWindow(client)
    client.game_window = game_window
    game_window.daemon=True
    game_window.start()
    client.start()
    
