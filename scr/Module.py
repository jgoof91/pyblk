import sys
import subprocess
import select
from enum import Enum


class Align(Enum):
    LEFT = 0
    CENTER = 0
    RIGHT = 0


class Module():
    def __init__(self, script, interval, signal, align=Align.RIGHT, order=-1):
        self.script = script
        self.interval = int(interval)
        self.signal = int(signal)
        self.align = align
        self.order = int(order)

        self.output = ''
        self.popen = None

        self.alive = False
        self.register = False


    def __str__(self):
        return f'{self.script:10} {self.interval:4} {self.signal:2} {self.align:5} {self.order:2}'


    @property
    def fileno(self):
        try:
            return self.popen.stdout.fileno()
        except ValueError as e:
            return -1


    @property
    def is_alive(self):
        if self.popen.poll() is None:
            self.alive = True
        else:
            self.alive = False
        return self.alive


    def kill(self):
        if not self.is_alive:
            return
        self.popen.terminate()
        try:
            self.popen.wait(5)
        except TimeoutError as e:
            self.popen.kill()
        self.alive = False


    def read(self):
        buff = self.popen.stdout.read()
        if not buff:
            return False
        self.output = buff.decode('UTF-8')
        return True
    

    def run(self):
        try:
            self.popen = subprocess.Popen(self.script, stdout=subprocess.PIPE)
            self.alive = True
            return self.fileno
        except ChildProcessError as e:
            self.alive = False
            sys.stderr.write(f'Error: Could not run \'{self.name}\' script\n')
        except FileNotFoundError as e:
            self.alive = False
            sys.stderr.write(f'Error: \'{self.script[2:].join(" ")}\' not found\n')
        except ValueError as e:
            self.alive = False
            sys.stderr.write(f'{e}\n')
        raise ChildProcessError

    @staticmethod
    def build_lemonbar_str(modules, sep):
        left = sep.join(sorted([x.output for x in modules if x.align == Align.LEFT], key=lambda m: m.order))
        center = sep.join(sorted([x.output for x in modules if x.align == Align.CENTER], key=lambda m: m.order))
        right = sep.join(sorted([x.output for x in modules if x.align == Align.RIGHT], key=lambda m: m.order))
        print([x.output for x in modules])
        if left == sep:
            left = ''
        if center == sep:
            center = ''
        if right == sep:
            right = ''
        return f'%{{l}}{left}%{{c}}{center}%{{r}}{right}'


    @staticmethod
    def find_modules_by_fileno(modules, fileno):
        for module in modules:
            if module.fileno == fileno:
                return module
