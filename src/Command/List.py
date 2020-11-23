from Module import Module
from Command import Command


class ListCommand(Command.Command):
    def __init__(self):
        super().__init__('list')
        self.group = self.subparser.add_mutually_execlusive_group()
        self.group.add_argument('-j', '--json', dest='json', action='store_true', help='output list of modules in json')
        self.group.add_argument('-c', '--csv', dest='csv', action='store_true', help='output list of modules in csv')

        self.subparser.add_argument('-d', '--delimiter', dest='delimiter', type=str, default=',', help='Use with -c, --csv options to change to delimiter used default=","')


    def exec(self, args, **kwargs):
        parse_args = Command.PARSER.parse_args(args)
        if parse_args.json:
            s = json.dumps({'modules': [x.json() for x in modules]})
        elif parse_args.csv:
            s = ''.join([x.csv(parse_args.delimiter) for x in modules])
        else:
            s = ''
            for module, count in enumerate(modules):
                s += f'{count:<2} {module}\n'
        return s.encode()
