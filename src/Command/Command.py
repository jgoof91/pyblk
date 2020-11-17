import argparse

class Command():
    PARSER = argparse.ArgumentParser()
    SUBPARSERS = None

    def __init__(self, name):
        if Command.SUBPARSERS is None:
            Command.SUBPARSERS = Command.PARSER.add_subparsers()
        self.subparser = Command.SUBPARSERS.add_parser(name)


    def exec(self, server, args):
        pass
