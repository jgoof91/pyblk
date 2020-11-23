import sys
import subprocess
import json
import csv
from enum import Enum


class Align(Enum):
    LEFT = 0
    CENTER = 0
    RIGHT = 0


class Module():
    def __init__(self, script, interval, signal, align, order):
        self.script = script
        self.interval = interval
        self.signal = signal
        self.align = align
        self.order = order

        self.output = ''
        self.popen = None

        self.alive = False
        self.register = False


    def __str__(self):
        return f'{self.script:<10} {self.interval:<4} {self.signal:<2} {self.align:<5} {self.order:<2}'


    @property
    def fileno(self):
        try:
            return self.popen.stdout.fileno()
        except ValueError as e:
            return -1


    @property
    def is_alive(self):
        if self.popen is None:
            self.alive = False
        elif self.popen.poll() is None:
            self.alive = True
        else:
            self.alive = False
        return self.alive


    def reap(self):
        if not self.is_alive:
            return
        self.popen.terminate()
        try:
            self.popen.wait(5)
        except TimeoutError as e:
            self.popen.kill()
            self.popen.wait()
        self.alive = False


    def read(self):
        if self.popen is None:
            return False
        out, _ = self.popen.communicate()
        self.output = out.decode(encoding='UTF-8')
        self.alive = False
        return True


    def exec(self, shell):
        try:
            self.popen = subprocess.Popen([shell, '-c', self.script], stdout=subprocess.PIPE)
            self.alive = True
            return self.fileno
        except ChildProcessError as e:
            self.alive = False
            sys.stderr.write(f'Error: Could not execute \'{self.name}\' script\n')
        except FileNotFoundError as e:
            self.alive = False
            sys.stderr.write(f'Error: \'{self.script[2:].join(" ")}\' not found\n')
        except ValueError as e:
            self.alive = False
            sys.stderr.write(f'Value Error\n')


    def csv(self, sep=','):
        d = [
                self.script,
                self.interval,
                self.signal,
                self.align,
                self.order,
                self.alive,
                self.register
                ]
        return sep.join(d) + '\n'


    def json(self):
        d = {
                'script': self.script,
                'interval': self.interval,
                'signal': self.signal,
                'align': self.align,
                'order': self.order,
                'status': self.alive,
                'register': self.register
                } 
        return json.dumps(d)


    @staticmethod
    def find_modules_by_fileno(modules, fileno):
        for module in modules:
            if module.fileno == -1:
                continue
            elif module.fileno == fileno:
                return module
        return None
