



from collections import OrderedDict
from multiprocessing import Manager
from multiprocessing.managers import BaseManager, DictProxy

class LruDict:

    def __init__(self, size, *args, **kwargs):
        self.__max_size = size
        self.__dict = OrderedDict(*args, **kwargs)

    def __getitem__(self, obj):
        a = self.__dict[obj]
        self.__dict.move_to_end(obj, last=False)
        return a

    def __setitem__(self, obj, val):
        self.__dict[obj] = val
        self.__dict.move_to_end(obj, last=False)
        while len(self.__dict) > self.__max_size:
            self.__dict.popitem(last=True)

    def __getattr__(self, name):
        return getattr(self.__dict, name)

    def __str__(self) -> str:
        return str(self.__dict)

    def __repr__(self) -> str:
        return repr(self.__dict)


if __name__ == '__main__':
    m = Manager()
    m.list()
    BaseManager.register('LruDict', LruDict, DictProxy)
    manager = BaseManager()

    with manager as m:
        l = m.LruDict(5)
        l["dsfsd"] = "dsf"
        print(str(l))
        for i in range(20):
            l[str(i)] = i * 2
        print(l)
