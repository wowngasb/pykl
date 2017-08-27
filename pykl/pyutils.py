#-*- coding: utf-8 -*-
import binascii
import re
import datetime

def _t():
    tmp = str(datetime.datetime.now())
    return tmp if len(tmp) >= 26 else tmp + '0' * (26 - len(tmp))
    
crc32_mod = lambda strin, num: (binascii.crc32(strin) & 0xffffffff) % num

is_ipv4 = lambda s, _re = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'): _re.match(s)

def try_int(strin, intc=set(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']), space=set([' ', '\r', '\n', '\t'])):
    intc_list = []
    for c in strin:
        if c in intc:
            intc_list.append(c)
        elif c not in space:
            break
    return int(''.join(intc_list)) if intc_list else 0


def singleton(cls):
    instances = {}
    def _singleton(*args, **kwds):
        if cls not in instances:
            instances[cls] = cls(*args, **kwds)
        return instances[cls]
    return _singleton

@singleton
class Config(object):
    def __init__(self, dict_in, **kwds):
        self.__dict__.update(dict_in)
        self.__dict__.update(kwds)

    def __getattr__(self, name):
        return self.__dict__.get(name.lower(), '')

    def __str__(self):
        return str(self.__dict__)
    
def main():
    pass

if __name__ == '__main__':
    main()

