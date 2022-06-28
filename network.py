import socket
from enum import Enum, auto
import json
import time


class NetworkClient:

    client_id = None
    last_ping = 0

    def __init__(self,
                 host=socket.gethostbyname(socket.gethostname()),
                 port=20550,
                 client_socket=None,
                 client_id=None):
        if not client_socket:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host = host
            self.port = port
            self.addr = (self.host, self.port)
            self.is_connected = False
        else:
            self.client = client_socket
            self.addr = client_socket.getpeername()
            self.host = self.addr[0]
            self.port = self.addr[1]
            self.is_connected = True
            self.last_ping = time.time()
        if client_id:
            self.client_id = client_id
        self.client.settimeout(30)

    def connect(self):
        self.client.settimeout(3)
        try:
            self.client.connect(self.addr)
            self.is_connected = True
        except socket.error as e:
            print("[NETWORK]", e)
        self.client.settimeout(30)

    def send(self, action, client_id=None, payload=None):
        try:
            msg = {"action": action}
            if client_id:
                msg["client_id"] = client_id
            if payload:
                msg["payload"] = payload
            self.client.send(json.dumps(msg).encode())
        except socket.error as e:
            print(e)

    def recv(self, size=2048):
        msg = self.client.recv(size).decode()
        jsons = self.splice_json(msg)
        msgs = []
        # [ {"action": 3, {"payload:" (1,2)}, {"action": 3, {"payload:" (1,2)} ]
        for single_msg in jsons:
            val = {"action": MessageID.FAIL.value}
            if not single_msg:
                val = {"action": MessageID.EMPTY.value}
                msgs.append(val)
                continue
            val["action"] = json.loads(single_msg)["action"]
            try:
                val["payload"] = json.loads(single_msg)["payload"]
            except KeyError:
                pass
            try:
                val["client_id"] = json.loads(single_msg)["client_id"]
            except KeyError:
                pass
            msgs.append(val)
        return msgs

    def position_of_equal_open_close(self, txt: str):
        parenthesis = 0

        i = 0
        # Strip is required because the first char needs to be an {
        for entry in txt.strip():
            if i > 0 and parenthesis == 0:
                return i
            if entry == '{':
                parenthesis += 1
            elif entry == '}':
                parenthesis -= 1

            i += 1

    def splice_json(self, input_text: str):
        copy_of_text = input_text.strip()

        arr = []
        pos = 0

        while pos is not None:
            pos = self.position_of_equal_open_close(copy_of_text)
            text = copy_of_text[0:pos]
            arr.append(text)
            copy_of_text = copy_of_text[pos:]

        return arr


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
    SHIP_SUNK = auto()
    GAME_OVER = auto()
    PING = auto()
    PRINT = auto()
    BOARD = auto()
    TIME_LEFT = auto()
    START_PLACE_PHASE = auto()
    END_PLACE_PHASE = auto()
    YOUR_TURN = auto()
    EMPTY = auto()

class FieldState(Enum):
    SHOT = auto()
    SHIP = auto()