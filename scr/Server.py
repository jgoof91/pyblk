import sys
import getopt
import socket
import select
import subprocess
import shlex
from Module import Module

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

        self.shell = SHELL
        #self.lemonbar = subprocess.Popen([self.shell, '-c', 'lemonbar'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.modules = []
        self.output = ''
        self.refresh = False


    def add(self, args):
        if not args:
            return b'Error: add not enough arguments'
        try:
            optlist, args = getopt.getopt(args, 'c:i:s:o:a:')
            for opt, arg in optlist:
                if opt == '-c':
                    script = [self.shell, '-c', arg]
                elif opt == '-i':
                    interval = arg
                elif opt == '-s':
                    signal = arg
                elif opt == '-o':
                    order = arg
                elif opt == '-a':
                    align = arg
            module = Module(script=script, interval=interval, signal=signal, align=align, order=order)
            self.run_module(module)
            self.modules.append(module)
        except getopt.GetoptError as e:
            return b'Error: add wrong arguments'
        return b'Ok'


    def command(self, conn):
        buff, ret = b'', ''
        while True:
            try:
                tmp = conn.recv(1024)
            except BlockingIOError as e:
                break
            if not tmp:
                break
            buff = b''.join([buff, tmp])
        buff = buff.decode('UTF-8').split('\0')
        cmd = buff[0].lower()
        args = buff[1:]
        if cmd in 'add':
            ret = self.add(args)
        elif cmd in 'remove':
            ret = self.remove(args)
        elif cmd in 'list':
            ret = self.list()
        #elif cmd in 'lemonbar'
        #   pass
           # ret = self.lemonbar(args)
        send_ret = conn.sendall(ret)
        if send_ret is not None:
            sys.stderr.write('Failed to send data to client')
        conn.close()


    def close(self):
        for _, v in self.conn_table.items():
            v.close()
        self.sock.close()


    def draw(self):
        self.output = Module.build_lemonbar_str(self.modules, '|')
        print(self.output+'\n')
        #self.lemonbar.communicate(input=self.output)


    def list(self):
        s = ''
        for i, module in enumerate(self.modules):
            s += f'{i:2} {module}\n'
        return s.encode()
        

    def loop(self):
        count = 0
        with select.epoll() as self.epoll:
            self.epoll.register(self.sock.fileno(), select.EPOLLIN | select.EPOLLET)
            while True:
                events = self.epoll.poll(timeout=1.0)
                for fileno, event in events:
                    if self.sock.fileno() == fileno:
                        conn, addr = self.sock.accept()
                        conn.setblocking(False)
                        self.conn_table[conn.fileno()] = conn
                        self.epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                    elif event & select.EPOLLIN:
                        if fileno not in self.conn_table:
                            module = Module.find_modules_by_fileno(self.modules, fileno)
                            if module is None:
                                continue
                            self.refresh = module.read()
                        elif fileno in self.conn_table:
                            self.command(self.conn_table[fileno])
                            self.epoll.unregister(fileno)
                            self.conn_table.pop(fileno)
                    elif event & select.EPOLLHUP or event & select.EPOLL_RDHUP:
                        if fileno in self.conn_table:
                            self.epoll.unregister(fileno)
                            self.conn_table[fileno].close()
                            self.conn_table.pop(fileno)
                    elif event & select.EPOLLERR:
                        exit(0)
                self.reap_module()
                self.update_modules(count)
                if self.refresh:
                    self.draw()
                count += 1


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
            if not module.is_alive:
                self.unregister_module(module)
                module.popen.stdout.close()


    def remove(self, args):
        for arg in args:
            try:
                idx = int(arg)
                if idx >= len(self.modules) or idx <= 0:
                    return f'Error: {idx} does not exist'.encode()
                self.unregister_modules(self.modules[idx])
                self.modules[idx].kill()
                self.modules.pop(idx)
            except ValueError as e:
                return f'Error: {arg} is not a int'.encode()


    def run_module(self, module):
        if module.register and not module.is_alive:
            self.unregister_module(module)
            module.popen.stdout.close()
        module.run()
        self.register_module(module)


    def update_modules(self, time):
        for module in self.modules:
            if module.interval != 0 and time % module.interval == 0:
                self.run_module(module)
