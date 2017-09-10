#-*- coding: utf-8 -*-

from sqlalchemy.ext.declarative.api import DeclarativeMeta

def int2bin(val, length=8, skip=4, seq=' '):
    bstr = bin(val).split('0b')[1]
    fstr = '0' * (length-len(bstr)) if len(bstr)<length else ''
    return '0b' + ''.join([char + seq if idx%skip==0 else char for idx, char in enumerate(list(fstr + bstr)[::-1])][::-1])

class BitMask(object):
    def __init__(self, val):
        self.val = val if isinstance(val, int) else int(val.replace(' ', ''), 2)

    def __repr__(self):
        return str(self.__class__).replace('>', ' ' + int2bin(self.val, 8) + '>')

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
