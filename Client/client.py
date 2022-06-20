import sys

print("Running Python version: " + str(sys.version))
from base64 import encode
import socket
import threading
import json
import time

from network import NetworkClient
from network import MessageID


class Client():

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
        print(self.network_client.client_id)
        print("Server accepted connection.")

    def join_queue(self):
        self.network_client.send(MessageID.ADD_QUEUE.value)
        msg = self.network_client.recv()
        print(msg)
        if not msg.get("action") == MessageID.OK.value:
            self.handle_failure("Error while joining queue.")
        print("Joined queue.")

    def ping(self):
        self.network_client.send(MessageID.PING.value)

    def wait_for_message(self):
        return self.network_client.recv()

    def join_game_server(self, msg):
        print("FINALLY!!")
        print(f"payload: {msg.get('payload')}")
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
                print("Server gone?")
                self.network_client.client.close()
                return
            print(f"\"{MessageID(msg.get('action'))}\" received!")
            match msg.get("action"):
                case MessageID.PING.value:
                    self.network_client.last_ping = time.time()
                    self.network_client.send(MessageID.PING.value)
                    print(f"Pong {self.network_client.client_id}")
                case MessageID.GAMESERVER.value:
                    self.join_game_server(msg)
                    break
                case MessageID.EMPTY.value:
                        print("Empty package case.")
                        print("Server gone. Purging.")
                        self.purge_client()
                        break
                case _:
                    print(f"Package \"{MessageID(msg.get('action'))}\" received!")


    def handle_failure(self, message="Received unexpected network package."):
        try:
            self.net.client.close()
        except:
            pass
        print(message)
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
