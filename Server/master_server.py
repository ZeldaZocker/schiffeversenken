from ast import match_case
from multiprocessing import connection
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
import uuid



class MasterServer():
    client_queue = []
    game_servers = []
    PREFIX = "[MASTER]"

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = host
        self.port = port
        self.addr = (self.server, self.port)
        self.is_running = False

    def start(self):
        self.is_running = True
        self.socket.bind(self.addr)
        self.socket.listen(30)
        self.thread = Thread(target=self.accept_new_connections, args=())
        self.thread.start()
        self.mainloop()

    def mainloop(self):
        while 1:
            print(self.PREFIX, len(self.client_queue))
            if len(self.client_queue) >= 2:
                addr = self.initGameServer()
                for i in range(2):
                    network_client = self.client_queue.pop(0)
                    network_client.send(MessageID.GAMESERVER.value, payload=addr)
                    try:
                        network_client.client.close()
                    except:
                        pass
            time.sleep(2)

    def accept_new_connections(self):
        while self.is_running:
            try:
                client_socket, addr = self.socket.accept()
                print(f"{self.PREFIX} Got connection from ip: {addr[0]} {addr[1]}")
                network_client = NetworkClient(client_socket=client_socket)
                Thread(target=self.handle_client, args=(network_client,)).start()
                network_client.send(MessageID.OK.value, payload=str(uuid.uuid4()))
            except socket.error:
                print("Socket error. Server closing?")
                return
            time.sleep(1)
            
    def handle_client(self, network_client):
        print(f"{self.PREFIX} started client handle")
        try:
            while self.is_running:
                print(f"{self.PREFIX} loop client handle")
                msg = network_client.recv()
                print(f"{self.PREFIX} Received msg: {msg}")
                match msg.get("action"):
                    case MessageID.ADD_QUEUE.value:
                        print(f"{self.PREFIX} Adding client to queue")
                        self.client_queue.append(network_client)
                        network_client.send(MessageID.OK.value)
                    case MessageID.LEAVE_QUEUE.value:
                        self.client_queue.remove(network_client)
                        network_client.send(MessageID.OK.value)
                    case MessageID.PING.value:
                        network_client.last_ping = time.time()
                    case MessageID.DISCONNECT.value:
                        client_id = msg.get("client_id")
                        print(f"{self.PREFIX} Client ({client_id}) disconnected by itself.")
                        self.purge_client(network_client)
                        break
                    case MessageID.EMPTY.value:
                        print(f"{self.PREFIX} Client disconnected by itself.")
                        self.purge_client(network_client)
                        break
                    case _:
                        print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")
                if network_client.last_ping + 10 < time.time():
                    network_client.send(MessageID.OK.value)
                    print(f"Ping {network_client.client_id}")

        except socket.error:
            print(f"{self.PREFIX} Client disconnected.")
            self.purge_client(network_client)

    def purge_client(self, network_client):
        try:
            self.client_queue.remove(network_client)
        except:
            pass
        try:
            network_client.send(MessageID.DISCONNECT.value)
        except:
            pass
        try:
            network_client.client.close()
        except:
            pass

    def initGameServer(self):
        port = random.randint(20560, 20999)
        host = socket.gethostname()
        addr = (host, port)
        game_server = GameServer(addr)
        Thread(target=game_server.start, args=()).start()
        self.game_servers.append(game_server)
        return addr

    def signal_handler(self, sig, frame):
        self.is_running = False
        self.socket.close()
        for c in self.client_queue:
            c.close()
            print(f"{self.PREFIX} Close connection to client.")
        for game_server in self.game_servers:
            game_server.stop()
        print(f"{self.PREFIX} You pressed Ctrl+C!")
        sys.exit(0)


if __name__ == '__main__':
    master = MasterServer(socket.gethostname(), 20550)
    signal.signal(signal.SIGINT, master.signal_handler)
    master.start()
