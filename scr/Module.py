import subprocess

class Module():
    def __init__(self, name, cmd, interval, signal):
        self.name = name
        self.cmd = cmd
        self.interval = interval
        self.signal = signal
        self.output = ''
        self.popen = None

    def run():
        self.popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
