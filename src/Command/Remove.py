from Module import Module
from Command import Command

class RemoveCommand(Command.Command):
    def __init__(self):
        super().__init__('remove')
        self.subparser.add_argument('-i', '--index', type=int, dest='index', help='Index of the module to remove. To get index run the list command.')


    def exec(self, args, **kwargs):
        parse_args = Command.PARSER.parse_args(args)
        if parse_args.index >= len(server.modules) or parse_args < 0:
            return b'index is greater or less than number of modules\n'
        module = modules[parse_args.index]
        epoll.unregister(module)
        module.reap()
        modules.pop(parse_args.index)
        return b'Ok\n'
