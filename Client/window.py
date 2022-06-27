from tkinter import *
from tkinter import messagebox
from threading import Thread
from board import *
import time


class GameWindow(Thread):
    is_destroyed = False
    DEFAULT_BG = "#404040"

    def __init__(self, client):
        Thread.__init__(self)
        self.client = client
        self.own_buttons = {}
        self.enemy_buttons = {}

    def run(self):
        self.root = Tk()
        self.root.title("Schiffe Versenken von Noah")
        self.root.geometry(f"{620*2+70}x680")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.configure(bg=self.DEFAULT_BG)

        self.button_frame = Frame(self.root,
                                  width=60 * 8,
                                  height=40,
                                  highlightbackground="red",
                                  highlightthickness=0,
                                  bg=self.DEFAULT_BG)
        self.button_frame.grid(row=0, column=0, columnspan=3)
        self.button_frame.grid_propagate(False)

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.rowconfigure(0, weight=1)

        text_frame = Frame(self.root,
                           width=60 * 8,
                           height=20,
                           bg=self.DEFAULT_BG)
        text_frame.grid(row=1, column=0, columnspan=3)
        text_frame.grid_propagate(False)

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.text = Label(text_frame,
                          text="You're not supposed to see this!",
                          font='Helvetica 9 bold',
                          fg="red",
                          bg=self.DEFAULT_BG)

        self.button = Button(self.button_frame,
                             bg="gray",
                             textvariable=StringVar(self.button_frame,
                                                    "Join Server"),
                             command=self.join_server_btn)
        self.button.grid(sticky="wens")

        spacer = Frame(self.root,
                       width=70,
                       height=60,
                       highlightbackground="yellow",
                       highlightthickness=4,
                       bg=self.DEFAULT_BG).grid(row=0, column=1, rowspan=3)

        button_list = []
        z = 0
        self.enemy_board_frame = Frame(self.root,
                                       width=620,
                                       height=620,
                                       bg=self.DEFAULT_BG,
                                       highlightbackground="red",
                                       highlightthickness=0)
        self.enemy_board_frame.grid_propagate(False)
        self.enemy_board_frame.grid(row=2, column=0)

        for y in range(10):
            for x in range(10):
                btnString = StringVar(self.enemy_board_frame, f"{x} {y}")
                frame = Frame(self.enemy_board_frame,
                              width=60,
                              height=60,
                              bg=self.DEFAULT_BG,
                              highlightbackground="blue",
                              highlightthickness=0)
                frame.grid_propagate(False)
                frame.columnconfigure(0, weight=1)
                frame.rowconfigure(0, weight=1)
                frame.grid(row=y, column=x, padx=1, pady=1)

                cmd = lambda x=x, y=y: self.client.shoot(x, y)
                #print(x,y)
                btn = Button(frame,
                             bg="gray",
                             textvariable=btnString,
                             command=cmd,
                             state=DISABLED)
                self.enemy_buttons[(x, y)] = btn
                btn.grid(sticky="wens")
                #btn.grid(row=i, column=z)
                button_list.append(btn)
        #self.board_frame.grid_remove()

        button_list = []
        z = 0
        self.own_board_frame = Frame(self.root,
                                     width=620,
                                     height=620,
                                     highlightbackground="red",
                                     highlightthickness=0)
        self.own_board_frame.grid_propagate(False)
        self.own_board_frame.grid(row=2, column=2)

        for y in range(10):
            for x in range(10):
                btnString = StringVar(self.own_board_frame, f"")
                frame = Frame(self.own_board_frame,
                              width=60,
                              height=60,
                              highlightbackground="blue",
                              highlightthickness=0)
                frame.grid_propagate(False)
                frame.columnconfigure(0, weight=1)
                frame.rowconfigure(0, weight=1)
                frame.grid(row=y, column=x, padx=1, pady=1)

                cmd = lambda x=x, y=y: self.client.shoot(x, y)
                #print(x,y)
                btn = Button(frame,
                             bg="gray",
                             textvariable=btnString,
                             state=DISABLED)
                self.own_buttons[(x, y)] = btn
                btn.grid(sticky="wens")
                #btn.grid(row=i, column=z)
                button_list.append(btn)
        #self.board_frame.grid_remove()

        self.root.mainloop()

    def join_server_btn(self):
        if not self.client.connect_to_master():
            self.text.config(text="Error connecting to server!", fg="red")
            self.text.pack()
            return
        thr = Thread(target=self.client.handle_message, args=())
        thr.start()

        self.button.configure(bg="gray",
                              textvariable=StringVar(self.button_frame,
                                                     "Join queue"),
                              command=self.join_queue_btn)

        self.text.config(text="Joined server.", fg="green")
        self.text.pack()

    def join_queue_btn(self):
        if not self.client.join_queue():
            self.text.config(text="Error joining queue!", fg="red")
            self.text.pack()
            return
        self.button.configure(bg="gray",
                              textvariable=StringVar(self.button_frame,
                                                     "Leave queue"),
                              command=self.leave_queue_btn)
        self.text.config(text="Joined queue. Waiting for players.", fg="green")
        self.text.pack()
        Thread(target=self.check_game_state, args=[]).start()

    def leave_queue_btn(self):
        pass

    def check_game_state(self):
        while self.client.is_running:
            print("Check state")
            if self.client.is_ingame:
                print("ingame state found")
                self.text.config(text="Connected to gameserver!", fg="green")
                self.button.configure(bg="gray",
                                      textvariable=StringVar(
                                          self.button_frame,
                                          "Randomize board"),
                                      command=self.generate_board)
                self.generate_board()
                return
            time.sleep(1)

    def generate_board(self):
        for _, btn in self.own_buttons.items():
            btn.configure(bg="gray", image="")

        photo = PhotoImage(file = r".\Client\ship_hit.png")

        self.client.generate_board()
        for ship in self.client.board.ships:
            color = ship.ship_type.get_color()
            for ship_field in ship.fields:
                self.own_buttons[(ship_field.x,
                                  ship_field.y)].configure(bg=color, image=photo)
                self.own_buttons[(ship_field.x, ship_field.y)].image = photo  # Needed to prevent garbage collection
                self.own_buttons[(ship_field.x, ship_field.y)].grid()

    def quit(self):
        self.root.quit()
        self.is_destroyed = True
        self.client.is_running = False
