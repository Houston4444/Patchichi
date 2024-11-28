
# This file is not used by the program
# It is just a file written for some tests,
# It could be removed, it will be soon.

import time
from typing import Callable, Any
import json
from pathlib import Path
import yaml

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


long_list = [i for i in range(100000)]

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

AMSTA = 'foulou'
AMSTAB = 'foulou'

def kiki_eq():
    for l in long_list:
        if AMSTA == AMSTAB:
            ...
            
def kiki_is():
    for l in long_list:
        if AMSTA is AMSTAB:
            ...
    

def reversed_int(num: int) -> int:
    return int(''.join(reversed([a for a in str(num)])))

def chilou(a):
    b = reversed_int(a)
    c = max(a, b) - min(a, b)
    return c + reversed_int(c)
    
for i in range(1000, 2000):
    print(i, ':', chilou(i))

# for path in dir.iterdir():
#     if not path.name ('.patchichi.json'):
#         continue

#     print(path)
#     with open(path, 'r') as file:
#         json_dict = json.load(file)
        
#     try:
#         version = tuple(json_dict.get('VERSION'))
#         if version >= (0, 2):
#             string = from_json_to_str(json_dict)
#             # print(string)
#             with open(path, 'w') as file:
#                 file.write(string)
#     except BaseException as e:
#         print('nonon')
#         print(str(e))
