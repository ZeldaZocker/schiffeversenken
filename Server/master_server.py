from ast import match_case
import socket
from threading import Thread
import random
from network import NetworkClient
from network import MessageID
from game_server import GameServer
import signal
import sys
import json
import time



class MasterServer():
    client_queue = []

    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = host
        self.port = port
        self.addr = (self.server, self.port)
        self.is_running = False

    def start(self):
        self.is_running = True
        self.client.bind(self.addr)
        self.client.listen(30)
        self.thread = Thread(target=self.accept_new_connections, args=())
        self.thread.start()
        self.mainloop()

    def mainloop(self):
        while 1:
            if len(self.client_queue) >= 2:
                self.initGameServer()
                for i in range(2):
                    client = self.client_queue.pop(0)
                    client.send(json.dumps({"action": MessageID.GAMESERVER.value}).encode())
                    client.close()

    def accept_new_connections(self):
        while self.is_running:
            try:
                c, addr = self.client.accept()
                Thread(target=self.handle_client, args=(c,)).start()
                c.send(json.dumps({"action": MessageID.OK.value}).encode())
                print(f"Got connection from ip: {addr[0]} {addr[1]}")
            except socket.error:
                print("Socket error. Server closing?")
                return
            
    def handle_client(self, connection):
        last_ping_in = time.time()
        last_ping_out = time.time()
        try:
            while self.is_running:
                msg = connection.recv(2048).decode()
                print(f"Received msg: {msg}")
                match json.loads(msg).get("action"):
                    case MessageID.ADD_QUEUE.value:
                        self.client_queue.append(connection)
                        connection.send(str.encode(MessageID.OK.name))
                    case MessageID.LEAVE_QUEUE.value:
                        self.client_queue.remove(connection)
                        connection.send(str.encode(MessageID.OK.name))
                    case MessageID.PING.value:
                        last_ping_in = time.time()
                        connection.send(str.encode(MessageID.OK.name))
        except socket.error:
            print("Client disconnected.")

    def initGameServer(self):
        port = random.randint(20560, 20999)
        host = socket.gethostname()
        server = GameServer(host, port)
        Thread(target=server.start, args=())

    def signal_handler(self, sig, frame):
        self.is_running = False
        self.client.close()
        for c in self.client_queue:
            c.close()
            print("Close connection to client.")
        print('You pressed Ctrl+C!')
        sys.exit(0)


if __name__ == '__main__':
    master = MasterServer(socket.gethostname(), 20550)
    signal.signal(signal.SIGINT, master.signal_handler)
    master.start()
