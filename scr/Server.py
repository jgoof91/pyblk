import socket
import select
import subprocess
from Module import Module

class Server()
    def __init__(self, SOCK_ADDR, shell):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(SOCK_ADDR)
        self.sock.setblocking(False)

        self.shell = shell
        self.lemonbar = subprocess.Popen([self.shell, '-c', 'lemonbar'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.modules = []
        self.output = ''
        self.refresh = False


    def draw(self):
        self.output = Module.build_lemonbar_str(self.modules)
        self.lemonbar.communicate(input=self.output)


    def loop():
        count = 1
        with select.epoll as epoll:
            conn_table = {}
            epoll.register(self.sock.fileno(), select.EPOLLIN | select.EPOLLET)
            while True:
                events = epoll.poll(1000)
                for fileno, event in events:
                    if self.sock.fileno() == fileno:
                        conn, addr = self.sock.accept()
                        conn_table[conn.fileno()] = [conn, addr]
                        epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                    elif event & select.EPOLLIN:
                        if fileno not in conn_table:
                            for module in Module.find_modules_by_fileno(self.modules, [x for x, _ in events]):
                                module.read()
                                self.refresh = True
                        else:
                            buff = ''
                            while True:
                                temp = conn.recv(1024)
                                if temp:
                                    buff += temp
                            if not buff:
                                continue
                            self.command(buff.decode('UTF-8').split('\0'))
                    self.reap(epoll)
                    self.update(count, epoll)
                    if self.refresh:
                        self.draw()
                    count += 1

    
    def reap(self, epoll):
        for module in self.modules:
            fileno = module.poll()
            if fileno is not None:
                epoll.unregister(fileno)


    def update(self, count, epoll):
        for module in self.modules:
            if count % self.module == 0:
                fileno = module.run()
                if fileno is not None:
                    epoll.register(fileno, select.EPOLLIN | select.EPOLLET)
