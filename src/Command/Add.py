import argparse
from Command import Command
from Module import Module, Align

class AddCommand(Command.Command):
    def __init__(self):
        super().__init__('add')
        self.subparser.add_argument('-c', '--command', type=str, dest='command', required=True, help='The command the modules runs.')
        self.subparser.add_argument('-i', '--interval', type=int, dest='interval', default=0, help='Seconds when to run module command.')
        self.subparser.add_argument('-s', '--signal', type=int, dest='signal', default=-1, help='The signal to trigger the module command.')
        self.subparser.add_argument('-a', '--align', type=Align, dest='align', choices=[Align.LEFT, Align.CENTER, Align.RIGHT], default=Align.RIGHT, help='Where to align the modules output.')
        self.subparser.add_argument('-o', '--order', type=int, dest='order', default=0, help='The placement of the module output according to the align.')


    def exec(self, args, **kwargs):
        parse_args = Command.Command.PARSER.parse_args(args)
        module = Module(parse_args.command, parse_args.interval, parse_args.signal, parse_args.align, parse_args.order)
        modules.append(module)
        module.exec(shell)
        epoll.register(module)
        return b'Ok'
