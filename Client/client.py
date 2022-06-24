from logging import root
import sys

print("Running Python version: " + str(sys.version))
from base64 import encode
import socket
import threading
import json
import time

from network import NetworkClient
from network import MessageID

from tkinter import *
from tkinter import messagebox


root = Tk()
root.title("Schiffe Versenken von Noah")
root.geometry("585x620")
root.resizable(False, False)


button_list = []
z = 0
for i in range(9):
    for z in range(9):
        btnString = StringVar(root, f"{i} {z}")
        btn = Button(root, height=3, width=7, bd=5, relief="ridge", bg="#33ccff", textvariable=btnString, command=None)
        btn.grid(row=i, column=z)
        button_list.append(btn)

            


root.mainloop()


class Client():

    PREFIX = "[CLIENT]"

    def start(self):
        self.connect_to_master()
        self.join_queue()
        self.handle_message()
                

    def connect_to_master(self):
        self.network_client = NetworkClient(socket.gethostname(), 20550)
        if not self.network_client.is_connected:
            self.handle_failure("Error connecting to master server. (Step 1)")
        message = self.network_client.recv()
        if not message.get('action') == MessageID.OK.value:
            self.handle_failure("Error connecting to master server. (Step 2)")
        self.network_client.client_id = message.get('payload')
        print(self.PREFIX, self.network_client.client_id)
        print("{self.PREFIX} Server accepted connection.")

    def join_queue(self):
        self.network_client.send(MessageID.ADD_QUEUE.value)
        msg = self.network_client.recv()
        print(self.PREFIX, msg)
        if not msg.get("action") == MessageID.OK.value:
            self.handle_failure("Error while joining queue.")
        print("{self.PREFIX} Joined queue.")

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
        msg = self.network_client.recv()
        if not msg.get("action") == MessageID.OK.value:
            self.handle_failure("Error while joining game server.")
        self.network_client.client_id = msg.get('payload')
        self.handle_message()

    def handle_message(self):
        while self.network_client.is_connected:
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
                case MessageID.EMPTY.value:
                        print("{self.PREFIX} Empty package case.")
                        print("{self.PREFIX} Server gone. Purging.")
                        self.purge_client()
                        break
                case _:
                    print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")

            if self.network_client.last_ping + 10 < time.time():
                self.network_client.send(MessageID.OK.value)


    def handle_failure(self, message="Received unexpected network package."):
        try:
            self.net.client.close()
        except:
            pass
        print(self.PREFIX, message)
        input("Press Enter to exit.")
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



if __name__ == '__main__':
    client = Client()
    client.start()
