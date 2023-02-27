

from typing import Iterator

PRE_ATTRIBUTES = (
    'OUTPUT',
    'INPUT',
    'AUDIO',
    'MIDI',
    'CV',
    'ALSA',
    'VIDEO',
    'PHYSICAL',
    '~PHYSICAL',
    'MONITOR',
    '~MONITOR',
    'TERMINAL',
    '~TERMINAL',
    'PORTGROUP',
    '~PORTGROUP',
    'SIGNAL_TYPE',
    '~SIGNAL_TYPE'
)

POST_ATTRIBUTES = (
    'PRETTY_NAME',
    'ORDER',
    'GUI_VISIBLE',
    'GUI_HIDDEN',
    'ICON_NAME',
    'CLIENT_ICON'
)

def split_params(input_str: str, split_equal=False,
                 get_splitter=False) -> Iterator[tuple[str, int, int, bool]]:
    w_str = ''
    w_start = 0
    anti_end = False
    is_value = False
    
    for i in range(len(input_str)):
        c = input_str[i]
        if c == ':' and not anti_end:
            if w_str:
                yield (w_str, w_start, i - 1, is_value)
            if get_splitter:
                yield(c, i, i, False)
            
            is_value = False
            w_str, w_start = '', i + 1

        elif split_equal and c == '=' and not is_value:
            yield (w_str, w_start, i - 1, False)
            if get_splitter:
                yield (c, i, i, False)
            is_value = True
            w_str, w_start = '', i + 1
        
        elif c == '\\':
            anti_end = True
        else:
            w_str += c
            anti_end = False
            
    if w_str:
        yield (w_str, w_start, i, is_value)


if __name__ == '__main__':
    for stro in [':kofz:zefko:', ':sdpfo:fkodf:fkeo', 'fokf:eprof:', ':zeokf:okef:"fkeoms:kfof":',
                 ':eporkg:ggkgor:erj\:erog:erp',
                 ':AUDIO:OUTPUT', ':normz:fkoe"fokef"',
                 ':ICON_NAME=application-pdf:PRETTY_NAME=rantanplan']:
        print('___', stro, '___')
        for strou in split_params(stro, split_equal=True):
            print(strou)