import sys
import subprocess
import select
from enum import Enum


class Align(Enum):
    LEFT = 0
    CENTER = 0
    RIGHT = 0


class Module():
    def __init__(self, name, script, interval, signal, align=Align.RIGHT, order=-1):
        self.name = name
        self.script = script
        self.interval = interval
        self.signal = signal
        self.align = align
        self.order = order

        self.output = ''
        self.popen = None


    def poll(self):
        if self.popen is None:
            return None
        ret = self.popen.poll()
        if ret is None:
            return None
        self.popen = None
        return self.popen.stdout.fileno()


    def read(self):
        if self.popen:
            try:
                buff = self.popen.read()
                if not buff:
                    return
                self.output = buff.decode('UTF-8')
            except BlockingIOError:
                return
    

    def run(self):
        if self.popen:
            return None
        try:
            self.popen = subprocess.Popen(script, stdout=subprocess.PIPE)
            return self.popen.stdout.fileno()
        except ChildProcessError as e:
            self.popen = None
            sys.stderr.write(f'Error: Could not run \'{self.name}\' script\n')
            return None
        except FileNotFoundError as e:
            self.popen = None
            sys.stderr.write(f'Error: \'{self.script[2:].join(' ')}\' not found\n')
            return None
        except ValueError as e:
            self.popen = None
            sys.stderr.write(f'{e}')
            return None


    @staticmethod
    def build_lemonbar_str(modules, sep):
        left = sep.join(sorted([x for x in modules if x.align == Align.LEFT], key=lambda m: m.order))
        center = sep.join(sorted([x for x in modules if x.align == Align.CENTER], key=lambda m: m.order))
        right = sep.join(sorted([x for x in modules if x.align == Align.RIGHT], key=lambda m: m.order))
        if left == sep:
            left = ''
        if center == sep:
            center = ''
        if right == sep:
            right = ''
        return f'%{{l}}{left}%{{c}}{center}%{{r}}{right}'

    @staticmethod
    def find_modules_by_fileno(modules, filenos):
        return [x for x in modules if x.popen.stdout.fileno() in filenos]
