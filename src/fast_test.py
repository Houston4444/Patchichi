
import time
from typing import Callable


lala = True
tata = ['chamo']

def normal_count():
    for i in range(1000000):
        if lala:
            ...

def count_is():
    for i in range(1000000):
        if lala is True:
            ...

def count_eq():
    for i in range(1000000):
        if lala == True:
            ...

def count_list_str():
    for i in range(1000000):
        if tata:
            ...


big_list = [(i, i+1) for i in range(1000000)]
oth_big_list = [(i, i+1) for i in range(1000000)]
big_set = set(big_list)


def list_in_list():
    for li in big_list:
        li in oth_big_list
        
def list_in_set():
    oth_big_set = set(oth_big_list)
    for li in big_list:
        li in oth_big_set

def parse_list():
    for i, j in big_list:
        ...

def parse_list_comp():
    [(i, j) for i, j in big_list]

def parse_set():
    # big_set = set(big_list)
    for i, j in big_set:
        ...

class Fa:
    def __init__(self):
        self._nimp = 'Ratata'
        
    def get_nimp(self) -> str:
        return self._nimp
    
fas = [Fa() for i in range(10000)]


def list_attr():
    for fa in fas:
        if fa._nimp:
            ...
            
def list_getter():
    for fa in fas:
        if fa.get_nimp():
            ...

def measure(callable: Callable):
    before = time.time()
    callable()
    after = time.time()
    print('tadam', after - before)
    
measure(list_attr)
measure(list_getter)
