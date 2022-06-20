import socket
from enum import Enum, auto
import json
import time


class NetworkClient:

    def __init__(self, host = socket.gethostname(), port = 20550, client_socket = None, client_id = None):
        if not client_socket:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host = host
            self.port = port
            self.addr = (self.host, self.port)
            self.is_connected = False
            self.connect()
        else:
            self.client = client_socket
            self.addr = client_socket.getpeername()
            self.host = self.addr[0]
            self.port = self.addr[1]
            self.is_connected = True
            self.last_ping = time.time()
        self.client.settimeout(30)
        

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.is_connected = True
        except socket.error as e:
            print(e)

    def send(self, action, client_id = None, payload = None):
        try:
            msg = {"action": action}
            if client_id:
                msg["client_id"] = client_id
            if payload:
                msg["payload"] = payload
            self.client.send(json.dumps(msg).encode())
        except socket.error as e:
            print(e)

    def recv(self, size = 2048):
        msg = self.client.recv(size).decode()
        val = {"action": MessageID.FAIL.value}
        if not msg: return {"action": MessageID.EMPTY.value}
        val["action"] = json.loads(msg)["action"]
        try:
            val["payload"] = json.loads(msg)["payload"]
        except KeyError:
            pass
        try:
            val["client_id"] = json.loads(msg)["client_id"]
        except KeyError:
            pass
        return val


class MessageID(Enum):
    INIT = auto()
    OK = auto()
    FAIL = auto()
    ADD_QUEUE = auto()
    LEAVE_QUEUE = auto()
    DISCONNECT = auto()
    GAMESERVER = auto()
    SHOOT = auto()
    SHOOT_RESULT = auto()
    GAME_OVER = auto()
    PING = auto()
    PRINT = auto()
    START_PLACE_PHASE = auto()
    END_PLACE_PHASE = auto()
    YOUR_TURN = auto()
    EMPTY = auto()