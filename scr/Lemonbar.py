from sys import stderr, exit
from subprocess import Popen, PIPE

class Lemonbar():
    def __init__(self, shell_cmd):
        self.lemonbar = None
        self.shell = None
        self.shell_cmd = shell_cmd
        self.alive = True

    
    def start(self, args):
        try:
            self.lemonbar = Popen(['lemonbar', *args], stdin=PIPE, stdout=PIPE)
            self.shell = Popen([self.shell_cmd], stdin=PIPE)
            self.alive = True
            return (self.lemonbar.stdin.fileno(), self.lemonbar.stdout.fileno())
        except ChildProcessError as e:
            stderr.write(f'Error: lemonbar or {self.shell_cmd} won\'t start.\n')
            exit(1)
        except FileNotFoundError as e:
            stderr.write(f'Error: lemonbar or {self.shell_cmd} binary wasn\'t found.\n')
            exit(1)


    def stop(self):
        try:
            self.lemonbar.terminate()
            self.lemonbar.wait(5)
        except TimeoutError as e:
            self.lemonbar.kill()
            self.lemonbar.wait()
        try:
            self.shell.terminate()
            self.shell.wait(5)
        except TimeoutError as e:
            self.shell.kill()
            self.shell.wait()
        self.alive = False


    def write_lemonbar(self, payload):
        self.lemonbar.stdin.write(payload)


    def write_shell(self):
        payload = self.lemonbar.stdout.read()
        self.shell.stdin.write(payload)
