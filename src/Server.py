import sys
import getopt
import socket
import select
import subprocess
import shlex
from Command import Add, Remove
from Module import Module, Align

class Server():
    def __init__(self, SOCK_ADDR, SHELL):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(SOCK_ADDR)
            self.sock.listen(1)
        except OSError as e:
            sys.stderr.write('Error: Address alreadly in use\n')
            exit(1)
        self.sock.setblocking(False)
        self.epoll = None
        self.conn_table = {}
        
        self.running = True
        self.shell = SHELL
        self.modules = []
        self.output = ''
        self.refresh = False

        self.command_dict = {
                'add': Add.AddCommand(),
                'remove': Remove.RemoveCommand()
                }


    def accept(self):
        conn, addr = self.sock.accept()
        conn.setblocking(False)
        self.conn_table[conn.fileno()] = conn
        self.epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)



    def command(self, conn):
        buff, ret = b'', ''
        while True:
            try:
                tmp = conn.recv(1024)
                if not tmp:
                    break
                buff = b''.join([buff, tmp])
            except BlockingIOError as e:
                break
        buff = buff.decode('UTF-8').split('\0')
        buff[0] = buff[0].lower()
        try:
            ret = self.command_dict[buff[0]].exec(self, buff)
        except KeyError as e:
            ret = f'{buff} does not exists\n'.encode()
        send_ret = conn.sendall(ret)
        if send_ret is not None:
            sys.stderr.write('Failed to send data to client\n')


    def close(self):
        for _, v in self.conn_table.items():
            v.close()
        self.sock.close()
        self.reap_module()


    def recv(self, fileno):
        if fileno in self.conn_table:
            self.command(self.conn_table[fileno])
            self.epoll.unregister(fileno)
            self.conn_table[fileno].close()
            self.conn_table.pop(fileno)
        else:
            module = Module.find_modules_by_fileno(self.modules, fileno)
            if module is None:
                return
            self.unregister_module(module)
            ret = module.read()
            if not self.refresh:
                self.refresh = ret


    def draw(self):
        print([x.output + '\n' for x in self.modules])


    def hangup(fileno):
        if fileno in self.conn_table:
            self.epoll.unregister(fileno)
            self.conn_table[fileno].close()
            self.conn_table.pop(fileno)
        else:
            module = Module.find_modules_by_fileno(self.modules, fileno)
            module.reap()
            self.unregister_module(module)


    def list(self):
        s = ''
        for i, module in enumerate(self.modules):
            s += f'{i:2} {module}\n'
        return s.encode()


    def loop(self):
        count = 0
        with select.epoll() as self.epoll:
            self.epoll.register(self.sock.fileno(), select.EPOLLIN | select.EPOLLET)
            while self.running:
                events = self.epoll.poll(1000)
                for fileno, event in events:
                    if self.sock.fileno() == fileno:
                        self.accept()
                    elif event & select.EPOLLIN:
                        self.recv(fileno)
                    elif event & select.EPOLLHUP or event & select.EPOLL_RDHUP:
                        self.hangup(fileno)
                    elif event & select.EPOLLERR:
                        sys.stderr.write(f'{fileno}\n')
                self.update_modules(count)
                count += 1
                if self.refresh:
                    self.draw()


    def register_module(self, module):
        if module.register:
            return
        self.epoll.register(module.fileno, select.EPOLLIN | select.EPOLLET)
        module.register = True


    def unregister_module(self, module):
        if not module.register:
            return
        self.epoll.unregister(module.fileno)
        module.register = False


    def reap_module(self):
        for module in self.modules:
            module.reap()


    def run_module(self, module):
        if module.is_alive:
            return
        module.run(self.shell)
        self.register_module(module)


    def update_modules(self, time):
        for module in self.modules:
            if module.interval != 0 and time % module.interval == 0:
                self.run_module(module)
