import socket
import sys
from network import MessageID
import time
from network import NetworkClient
from threading import Thread
import uuid


class GameServer():
    client_queue = []
    PREFIX = "[GAME]"

    def __init__(self, addr):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = addr[0]
        self.port = addr[1]
        self.addr = addr
        self.is_running = False

    def start(self):
        print("Started gameserver")
        self.socket.bind(self.addr)
        self.socket.listen(2)
        self.is_running = True
        Thread(target=self.ping_clients, args=()).start()
        while 1:
            try:
                client_socket, addr = self.socket.accept()
                print(f"{self.PREFIX} Got connection from ip: {addr[0]} {addr[1]}")
                network_client = NetworkClient(client_socket=client_socket)
                self.client_queue.append(network_client)
                Thread(target=self.handle_client, args=(network_client,)).start()
                id = str(uuid.uuid4())
                network_client.client_id = id
                network_client.send(MessageID.OK.value, payload=id)
            except socket.error:
                print(f"{self.PREFIX} Socket error. Server closing?")
                return
            time.sleep(1)
            if len(self.client_queue) > 2: #TODO
                self.start_game()

    def ping_clients(self):
        while self.is_running:
            for client in self.client_queue:
                try:
                    print(f"{self.PREFIX} Ping {client.client_id}")
                    client.send(MessageID.PING.value)
                except socket.error as e:
                    print(e)
            time.sleep(5)

    def handle_client(self, network_client):
        print(f"{self.PREFIX} started client handle")
        try:
            while self.is_running:
                print(f"{self.PREFIX} loop client handle")
                msg = network_client.recv()
                print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")
                match msg.get("action"):
                    case MessageID.PING.value:
                        network_client.last_ping = time.time()
                    case MessageID.DISCONNECT.value:
                        client_id = msg.get("client_id")
                        print(f"{self.PREFIX} Client ({client_id}) disconnected by itself.")
                        self.purge_client(network_client)
                        break
                    case MessageID.SHOOT.value:
                        pass
                    case MessageID.SHOOT_RESULT.value:
                        pass
                    case MessageID.SHOOT.value:
                        pass
                    case MessageID.EMPTY.value:
                        print(f"{self.PREFIX} Client disconnected by itself.")
                        self.purge_client(network_client)
                        break
                    case _:
                        print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")
                if network_client.last_ping + 10 < time.time():
                    network_client.send(MessageID.OK.value)
                    print(f"{self.PREFIX} Ping {network_client.client_id}")

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

    def start_game(self):
        print(f"{self.PREFIX} Starting game...")
        time.sleep(15)
        sys.exit()

    def stop(self):
        print(f"{self.PREFIX} Stopping game...")
        self.is_running = False
        for client in self.client_queue:
            try:
                client.send(MessageID.DISCONNECT.value)
            except:
                pass
            try:
                client.client.close()
            except:
                pass
        
if __name__ == "__main__":
    server = GameServer((socket.gethostname(), 25699))
    server.start()
