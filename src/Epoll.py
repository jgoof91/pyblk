from select import epoll, EPOLLET, EPOLLIN
from Module import Module

class Epoll():
    def __init__(self):
        self.epoll = epoll()


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.epoll.close()
        return True


    @property
    def closed(self):
        return self.epoll.closed


    def register(self, item):
        if item is Module:
            if item.register:
                return
            self.epoll.register(item.fileno, EPOLLET | EPOLLIN)
            print(f'register m {item}')
            item.register = True
        else:
            self.epoll.register(item, EPOLLET | EPOLLIN)
            print(f'register f {item}')


    def unregister(self, item):
        if item is Module:
            if not item.register:
                return
            self.epoll.unregister(item.fileno)
            print(f'unregister m {item}')
            item.register = False
        else:
            self.epoll.unregister(item)
            print(f'unregister f {item}')


    def poll(self, timeout):
        return self.epoll.poll(timeout)
