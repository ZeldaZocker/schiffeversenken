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

HOST = "10.106.112.71"   # "192.168.178.21"
PORT = 20550

class MasterServer():
    connected_clients = []
    client_threads = []
    client_queue = []
    game_servers = []
    PREFIX = "[MASTER]"
    PLAYERS_TO_START_GAMESERVER = 2

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
        print(f"{self.PREFIX} Started Master Server on {self.server}:{self.port}")
        self.connection_handle_thread = Thread(target=self.accept_new_connections, daemon=True, args=())
        self.connection_handle_thread.start()
        self.ping_thread = Thread(target=self.ping_clients, args=())
        self.ping_thread.start()
        self.mainloop()

    def mainloop(self):
        while self.is_running:
            #print(self.PREFIX, len(self.connected_clients), len(self.client_queue))
            if len(self.client_queue) >= self.PLAYERS_TO_START_GAMESERVER:
                addr = self.initGameServer()
                for i in range(self.PLAYERS_TO_START_GAMESERVER):
                    network_client = self.client_queue.pop(0)
                    print(f"{self.PREFIX} Send client to gameserver")
                    network_client.send(MessageID.GAMESERVER.value, payload=addr)
                    try:
                        network_client.client.close()
                    except:
                        pass
            for game_server in self.game_servers:
                if game_server.is_closeable:
                    self.game_servers.remove(game_server)
                    del(game_server)
            time.sleep(2)

    def accept_new_connections(self):
        while self.is_running:
            try:
                client_socket, addr = self.socket.accept()
                print(f"{self.PREFIX} Got connection from ip: {addr[0]} {addr[1]}")
                network_client = NetworkClient(client_socket=client_socket)
                network_client.connect()
                self.connected_clients.append(network_client)
                thread = Thread(target=self.handle_client, daemon=True, args=(network_client,))
                self.client_threads.append(thread)
                thread.start()
                id = str(uuid.uuid4())
                network_client.client_id = id
                network_client.send(MessageID.OK.value, payload=id)
            except socket.error:
                print(f"{self.PREFIX} Socket error while checking new connections. Server closing?")
                return
            time.sleep(1)
            
    def handle_client(self, network_client):
        print(f"{self.PREFIX} started client handle")
        try:
            while self.is_running:
                msgs = network_client.recv()
                for msg in msgs:
                    if not msg.get('action') == MessageID.PING.value:
                        print(f"{self.PREFIX} \"{MessageID(msg.get('action'))}\" received!")
                    match msg.get("action"):
                        case MessageID.ADD_QUEUE.value:
                            print(f"{self.PREFIX} Adding client to queue")
                            self.client_queue.append(network_client)
                            network_client.send(MessageID.ADD_QUEUE.value)
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
                    network_client.send(MessageID.PING.value)
                    #print(f"Ping {network_client.client_id}")
                time.sleep(0.05)
        except socket.error:
            print(f"{self.PREFIX} Client disconnected.")
            self.purge_client(network_client)

    def ping_clients(self):
        while self.is_running:
            for client in self.connected_clients:
                try:
                    #print(f"{self.PREFIX} Ping {client.client_id if client.client_id else 'Unknown ID'}")
                    client.send(MessageID.PING.value)
                except socket.error as e:
                    print(e)
            time.sleep(5)

    def purge_client(self, network_client):
        try:
            self.client_queue.remove(network_client)
        except:
            pass
        try:
            self.connected_clients.remove(network_client)
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
        host = HOST
        addr = (host, port)
        game_server = GameServer(addr)
        Thread(target=game_server.start, daemon=True, args=()).start()
        self.game_servers.append(game_server)
        print(f"{self.PREFIX} Started game server on {host}:{port}")
        return addr

    def signal_handler(self, sig, frame):
        print(f"{self.PREFIX} You pressed Ctrl+C!")
        self.is_running = False
        self.socket.close()
        for c in self.connected_clients:
            c.client.close()
            print(f"{self.PREFIX} Close connection to client.")
        for game_server in self.game_servers:
            game_server.stop()
        self.connection_handle_thread.join()
        self.ping_thread.join()
        for thr in self.client_threads:
            thr.join()
        sys.exit(0)


if __name__ == '__main__':
    master = MasterServer(HOST, PORT)
    signal.signal(signal.SIGINT, master.signal_handler)
    master.start()
