import socket


class BaseServer():
    def start(self):
        s = socket.socket()
        host = socket.gethostname()
        port = 20550
        s.bind((host, port))
        s.listen(30)

        while 1:
            c, addr = s.accept()
            print(f"Connected ip: {addr[0]}")
            self.client_queue.append(addr[0])
            c.send(b"Thx for connecting! We added you to the queue!")
            if len(self.client_queue) % 2 == 0:
                self.initGameServer()