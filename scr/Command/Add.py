import Command
import Module

import argparse


class Add(Command):
    def __init__(self, args):
        super().__init__(args)


    def exec(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-n', '--name', dest='name, 'type=str, required=True, help='Name of the module being add.')
        parser.add_argument('-c', '--command', dest='script', type=str, required=True, help='Command to exec for the module. This use you\'r SHELL.')
        parser.add_argument('-i', '--interval', dest='interval', type=int, default=0, help='The interval ')
        parser.add_argument('-s', '--signal', dest='signal', type=int, default=0, help='The signal to execute the module.')
        parser.add_argument('-a', '--align', dest='align', type=str, default='right', choices=['left', 'center', 'right'], help='The alignment of the module.')
        parser.add_argument('-o', '--order', dest='order', type=int, default=0, help='This determ the order of the module in accordance with the alignment')
        buff = parser.parse_args(self.args)
        return Module.Module(**buff)

