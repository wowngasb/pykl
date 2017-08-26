# -*- coding: UTF-8 -*-
import inspect
import re
from collections import namedtuple

__all__ = [
    'Error',
    'ValiDateException',
    'ValiConditionError',
    'nullOk',
    'multiType',
    'validParamDefault',
    'validParam',
    'vali3',
]

"""
@summary: 验证器
该模块提供了一个装饰器用于验证参数是否合法，使用方法为：
 
from pyvaild import validParam, nullOk, multiType

可能抛出的异常：
class ValiDateException(Error): #参数验证失败时抛出
    pass

class ValiConditionError(Error): #参数条件编译失败时抛出
    pass


@validParam(i=int)
def foo(i):
    return i+1
 
编写验证器：
 
1. 仅验证类型：
@validParam(type, ...)
例如：
检查第一个位置的参数是否为int类型：
@validParam(int)
检查名为x的参数是否为int类型：
@validParam(x=int)
 
验证多个参数：
@validParam(int, int)
指定参数名验证：
@validParam(int, s=str)
 
针对*和**参数编写的验证器将验证这些参数实际包含的每个元素：
@validParam(varargs=int)
def foo(*varargs): pass
 
@validParam(kws=int)
def foo7(s, **kws): pass
 
2. 带有条件的验证：
@validParam((type, condition), ...)
其中，condition是一个表达式字符串，使用x引用待验证的对象；
根据bool(表达式的值)判断是否通过验证，若计算表达式时抛出异常，视为失败。
例如：
验证一个10到20之间的整数：
@validParam(i=(int, '10<x<20'))
验证一个长度小于20的字符串：
@validParam(s=(str, 'len(x)<20'))
验证一个年龄小于20的学生：
@validParam(stu=(Student, 'x.age<20'))
 
另外，如果类型是字符串，condition还可以使用斜杠开头和结尾表示正则表达式匹配。
验证一个由数字组成的字符串：
@validParam(s=(str, '/^\d*$/'))
 
3. 以上验证方式默认为当值是None时验证失败。如果None是合法的参数，可以使用nullOk()。
nullOk()接受一个验证条件作为参数。
例如：
@validParam(i=nullOk(int))
@validParam(i=nullOk((int, '10<x<20')))
也可以简写为：
@validParam(i=nullOk(int, '10<x<20'))
 
4. 如果参数有多个合法的类型，可以使用multiType()。
multiType()可接受多个参数，每个参数都是一个验证条件。
例如：
@validParam(s=multiType(int, str))
@validParam(s=multiType((int, 'x>20'), nullOk(str, '/^\d+$/')))
 
5. 如果有更复杂的验证需求，还可以编写一个函数作为验证函数传入。
这个函数接收待验证的对象作为参数，根据bool(返回值)判断是否通过验证，抛出异常视为失败。
例如：
def validFunction(x):
    return isinstance(x, int) and x>0
@validParam(i=validFunction)
def foo(i): pass
 
这个验证函数等价于：
@validParam(i=(int, 'x>0'))
def foo(i): pass

6. 使用 validParamDefault 可以设置默认值，当参数验证不通过时，使用默认值代替原参数。
无默认值时会抛出异常。

例如：
@validParamDefault(i=(int, 'x>=0', 0))
def foo(i):
    return i + 1

foo(8)
>>9
foo('1')
>>1
foo(-1)
>>1

@author: HUXI
@since: 2011-3-22
@change: 2015-8-1
"""


class Error(Exception):
    pass

class ValiDateException(Error):
    pass

class ValiConditionError(Error):
    pass

#调试辅助函数
DBGS = lambda s:s.debug_log(s.info(s)) if hasattr(s,'debug_mode') and hasattr(s,'debug_log') and hasattr(s,'info') and s.debug_mode and s.debug_log and s.info else None



def _toStardardCondition(condition):
    func, default, _nullOk, _multiType  = __toStardardCondition(condition)
    if not _nullOk and default and default[0] is None:
        raise ValiConditionError("must use None as default with nullOk." % (con))
    def vali(x):
        f = func[0]
        if (_nullOk and x is None) or f[0](x):
            return (True, '', None)
        return (False, f[1], default)
    def _vali(x):
        if _nullOk and x is None:
            return (True, '', None)
        elif _multiType:
            es = []
            for f in func:
                if all([bool(ff[0](x)) for ff in f]):
                    return (True, '', None)
                es.append(','.join([ff[1] for ff in f]) )
            else:
                return (False, ' | '.join(es), default)
        else:
            for f in func:
                if not f[0](x):
                    return (False, f[1], default)
            else:
                return (True, '', None)
    return vali if len(func)==1 else _vali

def __toStardardCondition(con, default=None):
    func = []
    default = () if default is None else default
    if not con:
        raise ValiConditionError("condition is empty:%s." % (con))
    elif isinstance(con, (tuple, list)):
        cl = len(con)
        if cl==1:
            return __toStardardCondition(con[0], default=default)
        elif cl==3:
            return __toStardardCondition((con[0], con[1]), default=(con[2], ) )
        elif cl==2:
            _condition(con[0], con[1], func)
            func, default = tuple(func), tuple(default)
            return func, default, False, False
        else:
             raise ValiConditionError("condition error len:%s." % (con))
    elif inspect.isclass(con):
        return __toStardardCondition((con, None), default=default)
    elif inspect.isroutine(con):
        return __toStardardCondition((None, con), default=default)
    elif isinstance(con, dict):
        return con['func'], con['default'], con['_nullOk'], con['_multiType']
    else:
        raise ValiConditionError("condition not allow:%s." % (con))

def _condition(cls, con, func):
    if cls:
        if inspect.isclass(cls):
            f = lambda x: isinstance(x, cls)
            s = "type(@x) must %s" % (cls.__name__)
            func.append((f, s))
        else:
            _conditionEx(None, cls, func)
    if con:
        _conditionEx(cls, con, func)

def _conditionEx(cls, con, func):
    if isinstance(con, (tuple, list)):
        for con_item in con:
            _conditionEx(cls, con_item, func)
    elif cls in (str, unicode) and con[0] == con[-1] == '/':
        f = lambda x : isinstance(x, cls) and (re.match(con[1:-1], x) is not None)
        s = "@x re.match(%s)" % (con[1:-1] )
        func.append((f, s))
    elif inspect.isroutine(con):
        f = lambda x:con(x)
        s = "call %s(@x)" % (con)
        func.append((f, s))
    elif isinstance(con, str):
        con = con.strip()
        if not con:
	        f = lambda x:True
        elif inspect.isclass(cls):
        	f = lambda x:isinstance(x, cls) and eval(con)
        else:
	        f = lambda x:eval(con)
        s = "eval(%s) x=@x" % (con)
        func.append((f, s))
    else:
        raise ValiConditionError("condition error:%s." % (con))

class _validParam(object):

    def __init__(self, *varargs, **keywords):
        self.varargs = varargs
        self.keywords = keywords

        self._varargs = [_toStardardCondition(i) for i in varargs]
        self._keywords = {k:_toStardardCondition(v) for k,v in keywords.items()}

        self.all_valid = True
        self.use_default = False

        self.debug_log = None
        self.debug_mode = False

        self.set_return_key('__return__')

        self.info = lambda s, t=namedtuple("ValidInfo", ['varargs', 'keywords', 'fix_dctCallArgs', 'dctCallArgs', 'tupArgSpec', 'all_valid', 'use_default']):t(*(getattr(s, k, None) for k in t._fields))


    def set_return_key(self, rkey):
        self.return_key = rkey
        self.return_vali = self._keywords.pop(self.return_key, None)

    def __call__(self, user_function):
        tmp = _validParamEx(self)
        return tmp(user_function)


class _validParamEx(object):

    def __init__(self, obj):
        self.__dict__.update(obj.__dict__)
        self.__last = ()
    def getargspec(self, func):
        try:
            tmp = inspect.getargspec(func)
            return (tmp.args, tmp.varargs, tmp.keywords, tmp.defaults)
        except:
            tmp = inspect.getfullargspec(func)
            return (tmp.args, tmp.varargs, tmp.varkw, tmp.defaults)

    def __call__(self, func):

        def _getcallargs(args, varargname, kwname, default , varargs, keywords, all_args, other_args):
            dctArgs, callvarargs = {}, []
            keywords = dict(keywords)
            if default:
                defcount = len(default)
                for n,v in enumerate(default):
                    dctArgs[args[-(defcount-n)]] = v
            argcount = len(args)
            varcount = len(varargs)
            if argcount <= varcount:
                callvarargs = list(varargs[-argcount:])
                for n, argname in enumerate(args):
                    dctArgs[argname] = varargs[n]
            else:
                for n, var in enumerate(varargs):
                    dctArgs[args[n]] = var
                for argname in args[varcount:]:
                    if argname in keywords:
                        dctArgs[argname] = keywords.pop(argname)
            if other_args:
                if varargname is not None:
                    dctArgs[varargname] = callvarargs
                if kwname is not None:
                    dctArgs[kwname] = keywords
            else:
                if varargname in keywords:
                    dctArgs[varargname] = keywords.pop(varargname)
                if kwname in keywords:
                    dctArgs[kwname] = keywords.pop(kwname)
                if keywords:
                    raise TypeError("set not other_args , but keywords:%s." %(keywords))
            if keywords:
                args_set = set(args)
                for argname in keywords:
                    if argname in args_set:
                        raise TypeError("multi value for arg:%s." %(argname))
            if all_args:
                for argname in args:
                    if argname not in dctArgs:
                        raise TypeError("set all_args, but can not find arg:%s." %(argname))
            return dctArgs

        def _copy(self_dctCallArgs, varargname, kwname):
            dctCallArgs = {k:v for k,v in self_dctCallArgs.items() if k!=varargname or k!=kwname}
            if varargname is not None:
                dctCallArgs[varargname] = [i for i in self_dctCallArgs[varargname]]
            if kwname is not None:
                dctCallArgs[kwname] = {k:v for k,v in self_dctCallArgs[kwname].items()}
            return dctCallArgs

        self.tupArgSpec = self.getargspec(func)
        args, varargname, kwname, default = self.tupArgSpec
        self.dctValidator = _getcallargs(args, varargname, kwname, [], self._varargs, self._keywords, all_args=False, other_args=False)
        self.__last = (self.varargs, self.keywords, self.dctValidator,)
        self.dctCallArgs = {}
        self.fix_dctCallArgs = {}

        def wrapper(*callvarargs, **callkeywords):
            self.dctCallArgs = _getcallargs(args, varargname, kwname, default, callvarargs, callkeywords, all_args=True, other_args=True)
            dctCallArgs = _copy(self.dctCallArgs, varargname, kwname)

            def func_assert(func, k, vali, item):
                ret, estr, default = vali(item)
                if not ret:
                    if self.use_default and len(default)==1:
                        return default[0]
                    vstr = '`%s`<%s>' % (item, item.__class__.__name__)
                    estr = estr.replace('@x', vstr)
                    msg = "%s failed:%s=%s with [%s]" % (func.__name__, k, vstr, estr)
                    DBGS(self)
                    raise ValiDateException(msg)
                return item

            k, item = None, None
            for k, vali in self.dctValidator.items():
                if k == varargname:
                    for i, _ in enumerate(dctCallArgs[k]):
                        item = dctCallArgs[k][i]
                        dctCallArgs[k][i] = func_assert(func, k, vali, item)
                elif k == kwname:
                    for key in dctCallArgs[k]:
                        item = dctCallArgs[k][key]
                        dctCallArgs[k][key] = func_assert(func, k, vali, item)
                elif k in dctCallArgs:
                    item = dctCallArgs[k]
                    dctCallArgs[k] = func_assert(func, k, vali, item)
                elif k=='return':
                    pass
                else:
                    if self.all_valid:
                        DBGS(self)
                        raise TypeError("in validParam:%s can not find arg:%s." %(func.__name__, k))


            if self.use_default:
                self.fix_dctCallArgs = dctCallArgs
                args_fix = [dctCallArgs[k] for k in args]
                varargname_fix = dctCallArgs[varargname] if varargname is not None else ()
                kwname_fix = dctCallArgs[kwname] if kwname is not None else {}
                args_fix.extend(varargname_fix)
                callvarargs = tuple(args_fix)
                callkeywords = kwname_fix

            result = func(*callvarargs, **callkeywords)

            if self.return_vali is not None:
                tmp = func_assert(func, self.return_key, self.return_vali, result)
                result = tmp if self.use_default else result

            DBGS(self)
            return result

        def valid_info():
            return self.info(self)

        def valid_clear():
            valid_reset({})

        def valid_recover():
            if self.__last and len(self.__last)==3:
                self.varargs, self.keywords, self.dctValidator = self.__last

        def valid_reset(dctValidator, varargs=(), keywords={}):
            self.varargs, self.keywords, self.dctValidator = varargs, keywords, dctValidator

        def update_wrapper(wrapper_in, wrapped):
            for attr in ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__'):
                try: value = getattr(wrapped, attr)
                except AttributeError: pass
                else: setattr(wrapper_in, attr, value)
            for attr in ('__dict__',):
                getattr(wrapper_in, attr).update(getattr(wrapped, attr, {}))
            wrapper_in.__wrapped__ = wrapped
            return wrapper_in

        wrapper.valid_info = valid_info
        wrapper.valid_clear = valid_clear
        wrapper.valid_recover = valid_recover
        wrapper.valid_reset = valid_reset
        wrapper.valid_object = self
        return update_wrapper(wrapper, func)



#===============================================================================
#=================================TOOL==========================================
#===============================================================================
def nullOk(cls, con=None, default=None, use_default_none=False):
    func, default, _nullOk, _multiType  = __toStardardCondition((cls, con, default))  if (default is None and use_default_none) or default is not None else __toStardardCondition((cls, con))
    _nullOk = True
    return {'func':func, 'default':default, '_nullOk':_nullOk, '_multiType':_multiType }

def multiType(*con):
    func, default, _nullOk, _multiType = [], (), False, True
    for con_item in con:
        f, d, _n, _m  =  __toStardardCondition(con_item)
        if f:
            func.append(f)
        if d:
            default = d
        if _n:
            _nullOk = True
        if _m:
            raise ValiConditionError("multiType can not in multiType:%s." % (con))
    func, default = tuple(func), tuple(default)
    return {'func':func, 'default':default, '_nullOk':_nullOk, '_multiType':_multiType}

def validParamDefault(*varargs, **keywords):
    """函数修饰器 参数不满足条件时 使用设置的默认值替换参数，无默认值则 raise ValiDateException."""
    tmp = _validParam(*varargs, **keywords)
    tmp.use_default = True
    return tmp

def validParam(*varargs, **keywords):
    """函数修饰器 参数不满足条件时 raise ValiDateException."""
    tmp = _validParam(*varargs, **keywords)
    return tmp

def vali3(func):
    """python3.5 新特性  类型描述支持 def gcd(a: int, b: int) -> int:"""
    annotations = getattr(func, '__annotations__', None)
    varargs = ()
    keywords = annotations if annotations else {}
    tmp = validParam(*varargs, **keywords)
    tmp.debug_log = _LOG
    tmp.debug_mode = False
    tmp.set_return_key('return')
    return tmp(func)


def main(test_pre='_test'):
    #===============================================================================
    #=================================TEST==========================================
    #===============================================================================
    def _test1_simple():
        #检查第一个位置的参数是否为int类型：
        @validParam(int)
        def foo1(i): pass
        _unittest(foo1, (True, 1), (False, 's'), (False, None))

        #检查名为x的参数是否为int类型：
        @validParam(x=int)
        def foo2(s, x):
            pass
        _unittest(foo2, (True, 1, 2), (False, 's', 's'))

        #验证多个参数：
        @validParam(int, int)
        def foo3(s, x): pass
        _unittest(foo3, (True, 1, 2), (False, 's', 2))

        #指定参数名验证：
        @validParam(int, s=str)
        def foo4(i, s): pass
        _unittest(foo4, (True, 1, 'a'), (False, 's', 1))

        #针对*和**参数编写的验证器将验证这些参数包含的每个元素：
        @validParam(varargs=int)
        def foo5(*varargs): pass
        _unittest(foo5, (True, 1, 2, 3, 4, 5), (False, 'a', 1))

        @validParam(kws=int)
        def foo6(**kws): pass
        _functest(foo6, True, a=1, b=2)
        _functest(foo6, False, a='a', b=2)

        @validParam(kws=int)
        def foo7(s, **kws): pass
        _functest(foo7, True, s='a', a=1, b=2)

    def _test2_condition():
        #验证一个10到20之间的整数：
        @validParam(i=(int, ['10<x<20','x%2==1']))
        def foo1(x, i): pass
        _unittest(foo1, (True, 1, 11), (False, 1, 'a'), (False, 1, 12), (False, 1, 1))

        #验证一个长度小于20的字符串：
        @validParam(s=(str, 'len(x)<20'))
        def foo2(a, s): pass
        _unittest(foo2, (True, 1, 'a'), (False, 1, 1), (False, 1, 'a'*20))

        #验证一个年龄小于20的学生：
        class Student(object):
            def __init__(self, age): self.age=age

        @validParam(stu=(Student, 'x.age<20'))
        def foo3(stu): pass
        _unittest(foo3, (True, Student(18)), (False, 1), (False, Student(20)))

        #验证一个由数字组成的字符串：
        @validParam(s=(str, r'/^\d*$/'))
        def foo4(s): pass
        _unittest(foo4, (True, '1234'), (False, 1), (False, 'a1234'))

    def _test3_nullok():
        @validParam(i=nullOk(int))
        def foo1(i): pass
        _unittest(foo1, (True, 1), (False, 'a'), (True, None))

        @validParam(i=nullOk(int, '10<x<20'))
        def foo2(i): pass
        _unittest(foo2, (True, 11), (False, 'a'), (True, None), (False, 1))

    def _test4_multitype():
        @validParam(s=multiType(int, str))
        def foo1(s): pass
        _unittest(foo1, (True, 1), (True, 'a'), (False, None), (False, 1.1))

        @validParam(s=multiType((int, 'x>20'), nullOk(str, '/^\d+$/')))
        def foo2(s): pass
        _unittest(foo2, (False, 1), (False, 'a'), (True, None), (False, 1.1), (True, 21), (True, '21'))

    def _testd1_simple():
        """测试 带默认值 的验证"""
        #指定参数名验证：
        @validParamDefault((int,'',3), s=(str,'len(x)>1','xxx'), __return__ =(str))
        def foo4(i, s, c=0):
            _LOG("fix:i=%r,s=%r" % (i, s))
            return s*i
        _unittest(foo4, (True, 1, 'aa'), (True, 3, ''))

        #检查第一个位置的参数是否为int类型：
        @validParamDefault((int,'x>=3',3),__return__ =(nullOk(int)))
        def foo1(i):

            _LOG("fix:%r" % (i))
            if i>4:
                return 1
            else:
                return None
        _unittest(foo1, (True, 1),(True, 3),(True, 9), (True, 's'), (True, None))

        #检查名为x的参数是否为int类型：
        @validParamDefault(x=(int,'x>2',3))
        def foo2(s, x):
            _LOG("fix:s=%r,x=%r" % (s, x))
        _unittest(foo2, (True, 1, 0), (True, 's', 's'))

        #验证多个参数：
        @validParamDefault((int,'x>2',3), (int,'x>2',4))
        def foo3(s, x):
            _LOG("fix:s=%r,x=%r" % (s, x))
        _unittest(foo3, (True, 1, 2), (True, 's', 9))


        #针对*和**参数编写的验证器将验证这些参数包含的每个元素：
        @validParamDefault(varargs=(int,'4>x>2',3))
        def foo5(*varargs):
            _LOG("fix:varargs=%r" % (varargs, ))
        _unittest(foo5, (True, 1, 2, 3, 4, 5), (True, 'a', 'b', 'c', 1))

    def _test_py3():
        # python3.5 新特性  类型描述支持 def gcd(a: int, b: int) -> int:
        #@vali3
        #def gcd(a: int, b: int) -> int:
        @validParam(a=(int), b=(int), __return__=(int))
        def gcd(a, b):
            '''Return the greatest common divisor of a and b.'''
            a = abs(a)
            b = abs(b)
            if a < b:
                a, b = b, a
            while b != 0:
                a, b = b, a % b
            return a

        _unittest(gcd, (True, 1125, 495), (False, 6756, '342'), (False, 1.0, 9))

    ##==========TEST UNIT===========
    ## you must def your Error from Exception
    def _LOG(msg, handel=None):
        print(msg)

    def _unittest(func, *cases):
        return [_functest(func, *case) for case in cases]

    def _functest(func, isPass, *args, **kws):
        result = None
        try:
            _LOG('\n%s\n%s -> %s(args=%s,kws=%s)' %(func.valid_info(), isPass, func.__name__, args, kws))
            result = func(*args, **kws)
            _LOG('=%r' %(result ))
        except Error as ex:
            exn = '%s.%s' % (ex.__class__.__module__,ex.__class__.__name__)
            _LOG("%s -> %s:%s\n" %(isPass, exn, ex))
            if isPass:
                raise ex
        else:
            if not isPass:
                raise AssertionError("isPass:%s but no Exception!!!"%(isPass))
        return result

    g = locals()
    for k in [i for i in g]:
        if k.startswith(test_pre):
            _LOG( "\n\n>>%s" % (k,) )
            if hasattr(g[k], '__call__'):
                g[k]()

    _LOG("\n==========END===========")

if __name__ == '__main__':
    main()

