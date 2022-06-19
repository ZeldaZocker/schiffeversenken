import socket
from enum import Enum, auto


class NetworkClient:

    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = host
        self.port = port
        self.addr = (self.server, self.port)
        self.is_connected = False
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.is_connected = True
        except:
            pass

    def send(self, data):
        try:
            self.client.send(str.encode(data))
        except socket.error as e:
            print(e)


class MessageID(Enum):
    INIT = auto()
    OK = auto()
    FAIL = auto()
    ADD_QUEUE = auto()
    LEAVE_QUEUE = auto()
    GAMESERVER = auto()
    SHOOT = auto()
    SHOOT_RESULT = auto()
    GAME_OVER = auto()
    PING = auto()
    PRINT = auto()
    START_PLACE_PHASE = auto()
    END_PLACE_PHASE = auto()
    YOUR_TURN = auto()