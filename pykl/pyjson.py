# -*- coding: UTF-8 -*-
"""
json parse
@author:kl
@since: 2015-8-1
@change:
"""

__all__ = [
    'Error',
    'PyJsonTokenizeError',
    'PyJsonValueError',
    'PyJsonKeyError',
    'PyJsonMarkingError',
    'dump',
    'dumps',
    'load',
    'loads'
]

class Error(Exception):
    pass

class PyJsonTokenizeError(Error):
    pass

class PyJsonValueError(Error):
    pass

class PyJsonKeyError(Error):
    pass

class PyJsonMarkingError(Error):
    pass

def dump(obj, fp, *args, **kwgs):
    import json
    return json.dump(obj, fp, *args, **kwgs)

def dumps(obj, *args, **kwgs):
    import json
    return json.dumps(obj, *args, **kwgs)

def load(fp):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a JSON document) to a Python object.
    """
    return loads(fp.read())


def loads(s, strictmarking=True, strictkey=True, evaluation=None):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a JSON
    document) to a Python object.
    """
    s = s.strip()
    if not s:
        return None

    SYMBOL = ('{', '}', '[', ']', ':', ',')
    SPLIT = set(SYMBOL)
    SPACE = set(['\n', '\r', '\t', ' ', ])
    QUOTES = set(['"', "'", ])
    ESCAPE = '\\'
    TAG = (SPLIT, SPACE, QUOTES, ESCAPE)

    token_iter = _tokenize(s, TAG, evaluation=evaluation)
    obj, _ = _parse(s, token_iter, 0, SYMBOL, strictkey)
    tmp_list = list(token_iter.iterable) if token_iter.iterable else []
    if strictmarking and tmp_list:
        undo_list = [_get_token(s, token) for token in tmp_list]
        raise PyJsonMarkingError('%s undo list:%s' % (obj, undo_list))
    return obj

class IterTuple(object):
    def __init__(self, iterable, buffnum = 3):
        self.iterable = iterable
        self.cache_list = []
        self.cursor_s = 0
        self.cursor_e = 0
        self.buffnum = buffnum

    def __getitem__(self, index):
        if index < self.cursor_s:
            raise IndexError("cannot find index %d with cursor:(%d, %d)" % (index, self.cursor_s, self.cursor_e))
        while index + 1 > self.cursor_e and self.iterable:
            if len(self.cache_list) > self.buffnum:
                self.cursor_s += 1
                self.cache_list.pop(0)
            try:
                self.cache_list.append(next(self.iterable))
                self.cursor_e += 1
            except StopIteration:
                self.iterable = None
                break

        return self.cache_list[index - self.cursor_s]

def _tokenize(in_str, TAG, evaluation=None):
    """ return [ SPLIT->(index,), QUOTES->(index1, index2), VAL->(index1, index2, val<no space>), ...] """
    def ret_iter():
        SPLIT, SPACE, QUOTES, ESCAPE = TAG
        length = len(in_str)
        index = _skip(in_str, length, 0, SPACE)
        while index < length:
            c, _index = in_str[index], index
            if c in SPLIT:
                yield (_index,)  # SPLIT->(index,)
            elif c in QUOTES:
                index = _fstr(in_str, length, index, ESCAPE)
                yield (_index + 1, index)  # QUOTES->(index1, index2)
            else:
                index, val = _fval(in_str, length, index, SPLIT, SPACE)
                val = _value(val, (_index, index), evaluation)
                yield (_index, index, val,)  # VAL->(index1, index2, val<no space>)
                yield (index,)
            index = _skip(in_str, length, index + 1, SPACE)

    return IterTuple(ret_iter())


def _parse(in_str, token_list, index, SYMBOL, strictkey=True):
    DICT_L, DICT_R, LIST_L, LIST_R, KEY_T, JOIN_T = SYMBOL
    token = token_list[index]
    t_len = len(token)
    ret = None
    if t_len == 3:
        ret = token[2]
    elif t_len == 2:
        ret = in_str[token[0]:token[1]]
    elif t_len == 1:
        char = in_str[token[0]]
        if char == DICT_L:  # `{'key':val,...}`
            ret, index = {}, index + 1
            while not _symbol1(in_str, token_list[index], DICT_R):  # end while `}`
                _assert_key(in_str, token_list[index], ret, strictkey)  # assert next is `'key'`
                key, index = _parse(in_str, token_list, index, SYMBOL)
                _assert_s1(in_str, token_list[index], KEY_T)  # assert next is `:`
                val, index = _parse(in_str, token_list, index + 1, SYMBOL)
                _assert_s2(in_str, token_list[index], JOIN_T, DICT_R)  # assert next is `,` or `}`
                ret[key] = val
                if _symbol1(in_str, token_list[index], JOIN_T):  # pass next `,`
                    index += 1
        elif char == LIST_L:  # `[val,...]`
            ret, index = [], index + 1
            while not _symbol1(in_str, token_list[index], LIST_R):  # end while `]`
                val, index = _parse(in_str, token_list, index, SYMBOL)
                _assert_s2(in_str, token_list[index], JOIN_T, LIST_R)  # assert next is `,` or `]`
                ret.append(val)
                if _symbol1(in_str, token_list[index], JOIN_T):  # pass next `,`
                    index += 1
        else:
            raise PyJsonTokenizeError("can not match:%s@%s." % (char, token))
    else:
        raise PyJsonTokenizeError("can not do:%s" % (token))
    return ret, index + 1

def _evaluation(x, index, evaluation):
    try:
        return int(x)
    except ValueError, ex1:
        try:
            return float(x)
        except ValueError, ex2:
            if evaluation and hasattr(evaluation, '__call__'):
                return evaluation(x)
            else:
                msg = "Error value:%s@%s -> %s,%s." % (x, index, ex1, ex2,)
                raise PyJsonValueError(msg)

def _value(x, index, evaluation):
    if x == 'None' or x == 'null':
        return None
    elif x == 'True' or x == 'true':
        return True
    elif x == 'False' or x == 'false':
        return False
    else:
        return _evaluation(x, index, evaluation)

def _get_token(in_str, token):
    t_len = len(token)
    return in_str[token[0]] if t_len == 1 else \
            in_str[token[0]:token[1]] if t_len == 2 else \
            token[2] if t_len == 3 else None


def _skip(in_str, length, index, SPACE):
    """ return index of next char not space. """
    while index < length and in_str[index] in SPACE:
        index += 1
    return index


def _fstr(in_str, length, index, ESCAPE):
    """ in_str[index] is " or ', return index of next in_str[index] without \\ before it. """
    ci, index = in_str[index], index + 1
    while index < length and in_str[index] != ci:
        index += 2 if in_str[index] == ESCAPE else 1
    return index


def _fval(in_str, length, index, SPLIT, SPACE):
    """ in_str[index] is not symbol, return (index of next symbol, val without space). """
    val = []
    while index < length and in_str[index] not in SPLIT:
        if in_str[index] not in SPACE:
            val.append(in_str[index])
        index += 1
    return index, ''.join(val)

def _assert_s1(in_str, token, symbol):
    if not _symbol1(in_str, token, symbol):
        raise PyJsonTokenizeError("assert fails:%s@%s is %s." %
                          (_get_token(in_str, token), token, symbol))

def _symbol1(in_str, token, symbol):
    return len(token) == 1 and in_str[token[0]] == symbol

def _assert_s2(in_str, token, symbol1, symbol2):
    if not _symbol2(in_str, token, symbol1, symbol2):
        raise PyJsonTokenizeError(
            "assert fails:%s@%s is %s." % (_get_token(in_str, token), token,
                                           (symbol1, symbol2)))

def _symbol2(in_str, token, symbol1, symbol2):
    return len(token) == 1 and (in_str[token[0]] == symbol1 or
                                in_str[token[0]] == symbol2)

def _assert_key(in_str, token, rd, strictkey=True):
    itoken = _get_token(in_str, token)
    if len(token)==1:
        raise PyJsonTokenizeError("assert fails:%s@%s is symbol." % (itoken, token))
    if strictkey and len(token) != 2:
        raise PyJsonKeyError("assert fails:%s@%s is not str." % (itoken, token))
    if strictkey and itoken in rd:
        raise PyJsonKeyError(
            "assert fails:%s@%s is repkey in %s." % (itoken, token, rd))


##==========TEST UNIT===========

def main():
    import unittest

    class TestPyJsonLoad(unittest.TestCase):

        def test_strictmarking(self):
            args = '[34,4.56,],:{'
            self.assertRaises(PyJsonMarkingError, loads, args)
            self.assertEqual(loads(args, strictmarking=False), [34, 4.56])

            args = "{'a':0,'ac':[1,2,3],}[]"
            self.assertRaises(PyJsonMarkingError, loads, args)
            self.assertEqual(loads(args, strictmarking=False), {'a': 0, 'ac': [1, 2, 3]})

        def test_staic(self):
            args = '[None,null,True,true, {"v": true},false,False,{"f":False}]'
            self.assertEqual(loads(args), [None, None, True, True, {'v':True}, False, False, {'f':False}])

        def test_load_space(self):
            args = "    [4.   5,    [    ],   {'a'   : 'b',    }   ]"
            self.assertEqual(loads(args), [4.5, [], {'a':'b'}])

            args = '{\'test\':[\'fgh\',7  656,N  one,  Tr  ue,False  ,12  3.03  74,   7472e-9,98  e12,[1,2,\'daw"\', [None, True,], {\'a0\':.5346}]  ,{\'a\':1,\'b\':2,\'c\':3,},]  }'
            self.assertEqual(loads(args), {
                'test': [
                    'fgh', 7656, None, True, False, 123.0374, 7472e-9, 98e12,
                    [1, 2, 'daw"', [None, True], {'a0': 0.5346}],
                    {'a':1, 'b':2, 'c': 3}
                ]
            })

        def test_strictkey(self):
            args = '{76:554}'
            self.assertRaises(PyJsonKeyError, loads, args)
            self.assertEqual(loads(args, strictkey=False), {76: 554})

            args = "{'a':4,'a':[],}"
            self.assertRaises(PyJsonKeyError, loads, args)
            self.assertEqual(loads(args, strictkey=False), {'a': []})

        def test_dict(self):
            args_list = ['{}', '{ }']
            [self.assertEqual(loads(args), {}) for args in args_list]

            args_list = ["{'fg':556,}", "{'fg':556}", '{"fg":556}']
            [self.assertEqual(loads(args), {'fg': 556}) for args in args_list]

            args_list = ["{'a':123, 'b': 456}", "{'a':123, 'b': 456, }"]
            [self.assertEqual(loads(args), {'a': 123, 'b': 456}) for args in args_list]

            args_list = ['{,}', "{'fg':}", "{'fg',}", "{'fg':556]", "{'fg':556,,}", '{"123":,}', '{:"123"}', '{"a":"123":, "b":"123"}']
            [self.assertRaises(PyJsonTokenizeError, loads, args) for args in args_list]

            args_list = ['{"a":"123", "a":"123"}', '{123:"123"}']
            [self.assertRaises(PyJsonKeyError, loads, args) for args in args_list]

        def test_list(self):
            args_list = ['[]', '[ ]']
            [self.assertEqual(loads(args), []) for args in args_list]

            args_list = ['[12]', '[12, ]', '[12  , ]']
            [self.assertEqual(loads(args), [12]) for args in args_list]

            args_list = ["[34,56]", "[34,56,]", "[34,  56  ]"]
            [self.assertEqual(loads(args), [34,56]) for args in args_list]

            args = "['fgh',7656,None,True,False,123.0374,7472e-9,98e12,[],{},]"
            self.assertEqual(loads(args), ['fgh', 7656, None, True, False, 123.0374, 7.472e-06, 98000000000000.0, [], {}])

            args_list = ['[,]', "[34:]", "[34}", '[34,,]', "[34,,56]"]
            [self.assertRaises(PyJsonTokenizeError, loads, args) for args in args_list]

        def test_empty(self):
            args_list = ['', '  ', "\t \n   \r"]
            [self.assertEqual(loads(args), None) for args in args_list]

        def test_value(self):
            args = "{a:b,c     d:d, 'a ':123, 'c     d':' d' }['a']"
            self.assertRaises(PyJsonValueError, loads, args)
            self.assertRaises(PyJsonKeyError, loads, args, evaluation=lambda s: s)
            self.assertRaises(PyJsonMarkingError, loads, args, strictkey=False, evaluation=lambda s: s)
            self.assertEqual(loads(args, strictmarking=False, strictkey=False, evaluation=lambda s: s), {'a': 'b', 'a ': 123, 'c     d': ' d', 'cd': 'd'})

    globals()["TestPyJsonLoad"] = TestPyJsonLoad
    unittest.main(exit=False)
    exit(0)

if __name__ == '__main__':
    main()