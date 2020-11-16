import sys
import getopt
import socket
import select
import subprocess
import shlex
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


    def accept(self):
        conn, addr = self.sock.accept()
        conn.setblocking(False)
        self.conn_table[conn.fileno()] = conn
        self.epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)


    def add(self, args):
        if not args:
            return b'Error: add not enough arguments'
        try:
            module_args, msg = {}, b''
            optlist, args = getopt.getopt(args, 'c:i:s:o:a:')
            for opt, arg in optlist:
                if opt == '-c':
                    module_args['script'] = arg
                elif opt == '-i':
                    module_args['interval'] = arg
                elif opt == '-s':
                    module_args['signal'] = arg
                elif opt == '-o':
                    module_args['order'] = arg
                elif opt == '-a':
                    arg = arg.lower()
                    if 'l' in arg:
                        module_args['align'] = Align.LEFT
                    elif 'c' in arg:
                        module_args['align'] = Align.CENTER
                    elif 'r' in arg:
                        module_args['align'] = Align.RIGHT
                    else:
                        module_args['align'] = Align.RIGHT

            if 'script' not in module_args:
                msg = b'Add Error: script `-s` argument is need'
            else
                module = Module(**module_args)
                self.modules.append(module)
                self.run_module(module)
        except getopt.GetoptError as e:
            msg = b'Error: add wrong arguments'
        return msg if msg else b'Ok'


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
            sys.stderr.write('Failed to send data to client\n')


    def close(self):
        for _, v in self.conn_table.items():
            v.close()
        self.sock.close()
        self.reap_module()


    def recv(self, fileno):
        if fileno in self.conn_table:
            self.command(self.conn_table[fileno])
        else:
            module = Module.find_modules_by_fileno(self.modules, fileno)
            if module is None:
                return
            ret = module.read()
            self.unregister_module(module)
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
            module.kill()
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
                events = self.epoll.poll(timeout=1.0)
                for fileno, event in events:
                    if self.sock.fileno() == fileno:
                        self.accept()
                    elif event & select.EPOLLIN:
                        self.recv(fileno)
                    elif event & select.EPOLLHUP or event & select.EPOLL_RDHUP:
                        print('hangup')
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
            module.kill()


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
        if module.is_alive:
            return
        module.run()
        self.register_module(module)


    def update_modules(self, time):
        for module in self.modules:
            if module.interval != 0 and time % module.interval == 0:
                self.run_module(module)
