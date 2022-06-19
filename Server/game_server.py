import socket
import sys
from network import MessageID
import time


class GameServer():
    queue_size = 0
    client_queue = []

    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = host
        self.port = port
        self.addr = (self.server, self.port)
        self.is_running = False

    def start(self):
        self.client.bind(self.addr)
        self.client.listen(2)
        sys.exit()  # TODO
        while 1:
            c, addr = self.client.accept()
            print(f"Got connection from ip: {addr[0]}")
            self.client_queue.append(addr[0])
            c.send(str.encode(MessageID.OK.name))
            if len(self.client_queue) == 2:
                self.start_game()

    def start_game():
        print("Starting game...")
        time.sleep(15)
        sys.exit()
