import sys

print("Running Python version: " + str(sys.version))
from base64 import encode
import socket
import threading
import json

from network import NetworkClient
from network import MessageID


class Client():

    def start(self):
        self.connect_to_master()
        self.join_queue()
        self.join_game_server(self.wait_for_message())

    def connect_to_master(self):
        self.net = NetworkClient(socket.gethostname(), 20550)
        if not self.net.is_connected:
            self.handle_failure("Error connecting to master server. (Step 1)")
        message = json.loads(self.net.client.recv(2048).decode())
        print(message)
        if not message.get('action') == MessageID.OK.value:
            self.handle_failure("Error connecting to master server. (Step 2)")

    def join_queue(self):
        self.net.client.send(
            str.encode(json.dumps({"action": MessageID.ADD_QUEUE.value})))
        if not self.net.client.recv(2048).decode() == MessageID.OK.name:
            self.handle_failure("Error while joining queue.")

    def ping(self):
        self.net.client.send(
            str.encode(json.dumps({"action": MessageID.PING.value})))

    def wait_for_message(self):
        return self.net.client.recv(2048).decode()

    def join_game_server(self, message):
        action = json.loads(message).get('action')
        print(f"Message: {action}")
        if not action == MessageID.GAMESERVER.value:
            self.handle_failure()
        print("FINALLY!!")
        self.net.client.recv(2048).decode()
        self.net.client.close()
        self.handle_message(message)

    def handle_message(self, message):
        pass

    def handle_failure(self, message="Received unexpected network package."):
        print(message)
        input("Press Enter to exit.")
        sys.exit()


if __name__ == '__main__':
    client = Client()
    client.start()
