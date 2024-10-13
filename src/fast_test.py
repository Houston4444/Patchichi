
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
    

def from_json_to_str(input_dict: dict[str, Any]) -> str:
    '''for a canvas json dict ready to be saved,
    return a str containing the json contents with a 2 chars indentation
    and xy pos grouped on the same line.'''

    PATH_OPENING = 0
    PATH_IN = 1
    PATH_CLOSING = 2

    json_str = json.dumps(input_dict, indent=2)
    final_str = ''
    
    path = list[str]()
    path_step = PATH_IN
    
    for line in json_str.splitlines():
        strip = line.strip()
        
        if line.endswith(('{', '[')):
            path_name = ''
            if strip.startswith('"') and strip[:-1].endswith('": '):
                path_name = strip[1:-4]

            n_spaces = 0
            for c in line:
                if c != ' ':
                    break
                n_spaces += 1
            
            path = path[:(n_spaces // 2)]
            path.append(path_name)
            path_step = PATH_OPENING
        
        elif line.endswith(('],', ']', '},', '}')):
            path_step = PATH_CLOSING
        
        else:
            path_step = PATH_IN
        
        if len(path) >= 5 and path[1] == 'views':
            if len(path) == 5:
                if path_step in (PATH_OPENING, PATH_CLOSING):
                    final_str += line
                    final_str += '\n'
            
            elif len(path) == 6 and path[-1] == 'boxes':
                if path_step == PATH_IN:
                    final_str += line
                    final_str += '\n'
                    
            else:
                final_str += line
                final_str += '\n'
        # if len(path) 
        else:
            final_str += line
            final_str += '\n'

        if path_step == PATH_CLOSING:
            path = path[:-1]

    return final_str


# measure(kiki_eq)
# measure(kiki_is)
dir = Path('/home/houstonlzk5/.local/share/Patchichi/scenes/')
import yaml
path = dir / 'palouxe_yaml.patchichi.json.yaml'
with open(path, 'r') as f:
    poka = yaml.safe_load(f)
    
print(poka['editor_text'])
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
