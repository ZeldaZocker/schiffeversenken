import sys
from tkinter.ttk import Labelframe

print("Running Python version: " + str(sys.version))
from base64 import encode
import socket
from threading import Thread
import time
import signal

from network import NetworkClient, MessageID, FieldState
from window import GameWindow
from board import GameBoard



class Client():

    PREFIX = "[CLIENT]"
    is_running = False
    joined_queue = False
    game_window = None
    is_ingame = False
    game_started = False
    my_turn = False
    board = None
    HOST = "192.168.178.44"
    PORT = 20550
    time_until_start = 15

    def start(self):
        self.is_running = True
        while self.is_running:
            time.sleep(1)

    def connect_to_master(self):
        self.network_client = NetworkClient(self.HOST, self.PORT)
        self.network_client.connect()
        if not self.network_client.is_connected:
            print(f"{self.PREFIX} Error connecting to master server. (Step 1)")
            return False
        message = self.network_client.recv()
        if not message[0].get('action') == MessageID.OK.value:
            print(f"{self.PREFIX} Error connecting to master server. (Step 2)")
            self.purge_client()
            return False
        self.network_client.client_id = message[0].get('payload')
        print(self.PREFIX, self.network_client.client_id)
        print(f"{self.PREFIX} Server accepted connection.")
        return True

    def join_queue(self):
        self.network_client.send(MessageID.ADD_QUEUE.value)
        joined_queue_time = time.time()
        while not self.joined_queue:
            if time.time() - joined_queue_time > 10:
                print(f"{self.PREFIX} Error joining queue.")
                return False
        print(f"{self.PREFIX} Joined queue.")
        return True

    def ping(self):
        self.network_client.send(MessageID.PING.value)

    def join_game_server(self, msg):
        self.network_client.send(MessageID.DISCONNECT.value, client_id=self.network_client.client_id)
        self.network_client.client.close()
        self.network_client = NetworkClient(msg.get('payload')[0], msg.get('payload')[1])
        self.network_client.connect()
        msgs = self.network_client.recv()
        for msg in msgs:
            print(msg)
            if msg.get("action") == MessageID.OK.value:
                self.network_client.client_id = msg.get('payload')
                print(f"{self.PREFIX} Connected to gameserver!!")
                self.is_ingame = True
                return
        self.handle_failure("Error while joining game server.")
        

    def handle_message(self):
        try:
            while self.network_client.is_connected and self.is_running:
                msgs = self.network_client.recv()
                for msg in msgs:
                    if not msg:
                        print(f"{self.PREFIX} Server gone?")
                        self.network_client.client.close()
                        return
                    if not msg.get('action') == MessageID.PING.value:
                        print(f"{self.PREFIX} \"{MessageID(msg.get('action'))}\" received!")
                    match msg.get("action"):
                        case MessageID.PING.value:
                            self.network_client.last_ping = time.time()
                            self.network_client.send(MessageID.PING.value)
                            #print(f"{self.PREFIX} Pong {self.network_client.client_id}")
                        case MessageID.GAMESERVER.value:
                            self.join_game_server(msg)
                        case MessageID.ADD_QUEUE.value:
                            self.joined_queue = True
                        case MessageID.EMPTY.value:
                                print(f"{self.PREFIX} Empty package case.")
                                self.handle_failure("Server gone. Purging.")
                        case MessageID.DISCONNECT.value:
                            self.handle_failure("Received disconnect package. Purging.")
                        case MessageID.SHOOT.value:
                            x = msg.get("payload").get("x")
                            y = msg.get("payload").get("y")
                            if x == -1 and y == -1:
                                self.my_turn = True
                                print("I have the starting turn.")
                                continue
                            game_over = False
                            ship_hit = False
                            for ship in self.board.ships:
                                if ship_hit: break
                                for field in ship.fields:
                                    if ship_hit: break
                                    if field.x == x and field.y == y:
                                        field.shot = True
                                        self.network_client.send(MessageID.SHOOT_RESULT.value, payload={"result": FieldState.SHIP.value, "x":x,"y":y})
                                        game_window.own_buttons[(x,y)].configure(image=game_window.image_hit)
                                        ship_hit = True
                                        field_alive = False
                                        fields = []
                                        for field in ship.fields:
                                            if not field.shot:
                                                field_alive = True
                                                break
                                            fields.append((field.x, field.y))
                                        if not field_alive:
                                            self.network_client.send(MessageID.SHIP_SUNK.value, payload={"fields": fields})
                                            ship.destroyed = True
                                            for fld in fields:
                                                self.game_window.own_buttons[fld[0], fld[1]].configure(image=game_window.image_hit_gold)

                                        # Check for all ships destoryes
                                        game_over = True
                                        for ship in self.board.ships:
                                            if not ship.destroyed:
                                                game_over = False
                                                break
                                        if game_over:
                                             self.network_client.send(MessageID.GAME_OVER.value)
                                             self.game_window.text.configure(text="You lost the game.", fg = "red")
                                        break
                            if not ship_hit:
                                self.network_client.send(MessageID.SHOOT_RESULT.value, payload={"result": FieldState.SHOT.value, "x":x,"y":y})
                                self.game_window.own_buttons[(x,y)].configure(image=game_window.image_miss)
                            if not game_over:
                                self.my_turn = True
                        case MessageID.SHOOT_RESULT.value:
                            result = msg.get("payload").get("result")
                            x = msg.get("payload").get("x")
                            y = msg.get("payload").get("y")
                            if result == FieldState.SHIP.value:
                                print(f"{self.PREFIX} Ship hit. Yeah!")
                                self.game_window.enemy_buttons[(x,y)].configure(image=game_window.image_hit)
                            else:
                                print(f"{self.PREFIX} Ship missed. Sadge!")
                                self.game_window.enemy_buttons[(x,y)].configure(image=game_window.image_miss)
                        case MessageID.SHIP_SUNK.value:
                            print(msg.get("payload").get("fields"))
                            for field in msg.get("payload").get("fields"):
                                self.game_window.enemy_buttons[(field[0],field[1])].configure(image=game_window.image_hit_gold)
                        case MessageID.TIME_LEFT.value:
                            self.time_until_start = msg.get("payload").get("time")
                        case MessageID.END_PLACE_PHASE.value:
                            self.game_started = True
                        case MessageID.GAME_OVER.value:
                            self.game_window.text.configure(text="You won the game!", fg = "yellow")
                        case _:
                            print(f"{self.PREFIX} Package \"{MessageID(msg.get('action'))}\" received!")
                if self.network_client.last_ping + 10 < time.time():
                    self.network_client.send(MessageID.PING.value)
                time.sleep(0.1)
        except socket.error:
            print(f"{self.PREFIX} Server gone?.")
            self.purge_client()


    def handle_failure(self, message="Received unexpected network package."):
        self.purge_client()
        self.network_client.is_connected = False
        self.is_running = False
        if not self.game_window.is_destroyed:
            self.game_window.quit()
        print(self.PREFIX, message)
        input(f"{self.PREFIX} Press Enter to exit.")
        sys.exit()

    def purge_client(self):
        try:
            self.network_client.send(MessageID.DISCONNECT.value)
        except:
            pass
        try:
            self.network_client.client.close()
        except:
            pass

    def signal_handler(self, sig, frame):
        print(f"{self.PREFIX} You pressed Ctrl+C!")
        self.is_running = False
        self.purge_client()
        self.game_window.quit()
        sys.exit(0)

    def generate_board(self):
        self.board = GameBoard()
        self.board.clear_board()
        self.board.gernerate_board()

    def shoot(self, x, y):
        if not self.my_turn: return
        print(f"Shooting: {x} {y}")
        self.my_turn = False
        self.game_window.disable_buttons()
        del(self.game_window.enemy_untested_buttons[(x,y)])
        self.network_client.send(MessageID.SHOOT.value, payload={"x": x, "y": y})
        

    


if __name__ == '__main__':
    client = Client()
    signal.signal(signal.SIGINT, client.signal_handler)
    game_window = GameWindow(client)
    client.game_window = game_window
    game_window.daemon=True
    game_window.start()
    client.start()
    
