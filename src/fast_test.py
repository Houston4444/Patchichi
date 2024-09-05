
import time
from typing import Callable


class Pali:
    def __init__(self, name: str) -> None:
        self.name = name

class Chani:
    def __init__(self, pali: Pali):
        self.pali = pali

    def __enter__(self):
        print('cabouli')
        return self.pali
        
    def __exit__(self, *args, **kwargs):
        print('sortie')


long_list = [i for i in range(1000000)]

def direct_search():
    i = 999999
    if i in long_list:
        ...
        
def setted_search():
    i = 999999
    long_set = set(long_list)
    if i in long_list:
        ...

def measure(callable: Callable):
    before = time.time()
    callable()
    after = time.time()
    print('tadam', after - before)


measure(direct_search)
measure(setted_search)