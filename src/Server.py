import sys
import getopt
import socket
import subprocess
import shlex
from Command import Add, Remove
from Module import Module, Align
from Epoll import Epoll

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
                'remove': Remove.RemoveCommand(),
#                'list': List.ListCommand()
                }


    def accept(self):
        conn, addr = self.sock.accept()
        conn.setblocking(False)
        self.conn_table[conn.fileno()] = conn
        self.epoll.register(conn.fileno())


    def command(self, fileno, buff):
        ret = b''
        conn = self.conn_table[fileno]
        try:
            if 'add' in buff[0]:
                ret = self.command_dict['add'].exec(buff, modules=self.modules, epoll=self.epoll, shell=self.shell)
            elif 'remove' in buff[0]:
                ret = self.command_dict['remove'].exec(buff, modules=self.modules, epoll=self.epoll)
            #  elif 'list' in buff[0]:
                #  ret = self.command_dict['list'].exec(buff, modules=self.modules)
        except KeyError as e:
            ret = f'{buff} does not exists\n'.encode()
        ret = conn.sendall(ret)
        if ret is not None:
            sys.stderr.write('Failed to send data to client\n')


    def close(self):
        for _, v in self.conn_table.items():
            v.close()
        self.sock.close()
        self.reap_module()


    def read_socket(self, fileno):
        buff = b''
        conn = self.conn_table[fileno]
        while True:
            try:
                tmp = conn.recv(1024)
                print(tmp)
                if not tmp:
                    break
                buff = b''.join([buff, tmp])
            except BlockingIOError as e:
                break
        print(buff)
        buff = buff.decode('UTF-8').split('\0')
        buff[0] = buff[0].lower()
        return buff


    def recv(self, fileno):
        if fileno in self.conn_table:
            try:
                buff = self.read_socket(fileno)
                self.command(fileno, buff)
                self.epoll.unregister(fileno)
                self.conn_table[fileno].close()
                self.conn_table.pop(fileno)
            except Exception as e:
                print(f'{e}')
        else:
            module = Module.find_modules_by_fileno(self.modules, fileno)
            if module is None:
                return
            self.epoll.unregister(module)
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
            self.epoll.unregister(module)


    def list(self):
        s = ''
        for i, module in enumerate(self.modules):
            s += f'{i:2} {module}\n'
        return s.encode()


    def loop(self):
        count = 0
        with Epoll() as self.epoll:
            self.epoll.register(self.sock.fileno())
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


    def reap_module(self):
        for module in self.modules:
            module.reap()


    def exec_module(self, module):
        if module.is_alive:
            return
        module.exec(self.shell)
        self.epoll.register(module)


    def update_modules(self, time):
        for module in self.modules:
            if module.interval != 0 and time % module.interval == 0:
                self.exec_module(module)
