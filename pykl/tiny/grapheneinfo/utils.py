#-*- coding: utf-8 -*-
from sqlalchemy.inspection import inspect as sqlalchemyinspect
from sqlalchemy.ext.declarative.api import DeclarativeMeta

def int2bin(val, length=8, skip=4, seq=' '):
    bstr = bin(val).split('0b')[1]
    fstr = '0' * (length-len(bstr)) if len(bstr)<length else ''
    ostr = '0b' + ''.join([char + seq if idx%skip==0 else char for idx, char in enumerate(list(fstr + bstr)[::-1])][::-1])
    return ostr.strip()

def upper_tuple(r_list):
    if isinstance(r_list, dict):
        return [(k.strip().upper(), v) for k, v in r_list.items()]

    return [(i.strip().upper(), i.strip()) for i in r_list if i.strip()]

def mask_field(dao, bit_mask, inspect=True):
    inspected_model = sqlalchemyinspect(dao) if inspect else dao

    ret = {}
    for name, column in inspected_model.columns.items():
        info = getattr(column, 'info', None)
        if isinstance(info, BitMask):
            if info.has(bit_mask):
                ret[name] = column
    return ret

def mask_keys(dao, bit_mask, inspect=True):
    ret = mask_field(dao, bit_mask, inspect)
    return ret.keys()

class BitMask(object):
    def __init__(self, val, info=None):
        self.val = val if isinstance(val, int) else \
                    val.val if isinstance(val, self.__class__) else \
                        int(val.replace(' ', ''), 2)
        self._info = info

    def __repr__(self):
        return str(self.__class__).replace('>', ' ' + int2bin(self.val, 8) + '>')

    def __str__(self):
        return int2bin(self.val, 8)

    def __lshift__(self, other):
        '''实现使用 << 的按位左移动'''
        return self.__class__(self.val << other)

    def __rshift__(self, other):
        '''实现使用 >> 的按位左移动'''
        return self.__class__(self.val >> other)

    def __and__(self, other):
        '''实现使用 & 的按位与'''
        return self.__class__(self.val & (other.val if isinstance(other, self.__class__) else other))

    def __or__(self, other):
        '''实现使用 | 的按位或'''
        return self.__class__(self.val | (other.val if isinstance(other, self.__class__) else other))

    def __xor__(self, other):
        '''实现使用 ^ 的按位异或'''
        return self.__class__(self.val ^ (other.val if isinstance(other, self.__class__) else other))

    def __eq__(self, other):
        return self.val == (other.val if isinstance(other, self.__class__) else other)

    def __nonzero__(self):
        return bool(self.val)

    def has(self, other):
        '''判断包含关系 A.has(B) 表示A包含B中所有的非零位'''
        return (other & self) == other

HiddenField = BitMask('0b0000 0001')
InitializeField = BitMask('0b0000 0010')
EditableField = BitMask('0b0000 0100')
SortableField = BitMask('0b0000 1000')
CustomField = InitializeField | EditableField

def get_session(context):
    return context.get('session')


def get_query(model, context):
    query = getattr(model, 'query', None)
    if not query:
        session = get_session(context)
        if not session:
            raise Exception('A query in the model Base or a session in the schema is required for querying.\n'
                            'Read more http://graphene-python.org/docs/sqlalchemy/tips/#querying')
        query = session.query(model)
    return query


def is_mapped(obj):
    return isinstance(obj, DeclarativeMeta)
