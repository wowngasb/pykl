#-*- coding: utf-8 -*-
import re
import os
import time
import json

import graphql

from jinja2 import Template

def render_template_file(path, file_name, **context):
    file_path = os.path.join(os.path.dirname(__file__), path, file_name)
    with open(file_path, 'r') as rf:
        tpl_str = rf.read().decode('utf-8')
        template = Template(tpl_str)
        template.globals['time'] = time
        template.globals['json'] = json
        template.globals['len'] = len
        template.globals['str'] = str
        return template.render(**context)

_is_base = lambda v: v in (graphql.type.GraphQLID, graphql.type.GraphQLInt, graphql.type.GraphQLFloat, graphql.type.GraphQLBoolean, graphql.type.GraphQLString)
_is_enum = lambda v: isinstance(v, graphql.type.GraphQLEnumType)
_is_union = lambda v: isinstance(v, graphql.type.GraphQLUnionType)
_is_sqlalchemy = lambda v: hasattr(v.graphene_type, '_meta') and hasattr(v.graphene_type._meta, 'sqlalchemy_fields')
_is_abstract_sqlalchemy = lambda v: _is_sqlalchemy(v) and \
                            hasattr(v.graphene_type._meta, 'local_fields') and \
                                v.graphene_type._meta.local_fields

_is_simple = lambda v: _is_base(v) or _is_enum(v)

def _php_namespace(base, func=lambda p: p):
    def __php_namespace(path, b=base, f=func):
        tmp = f(path)
        tmp = ('\\' + tmp) if tmp else ''
        tmp = (b + tmp).replace('/', '\\')
        while tmp.find('\\\\') >= 0:
            tmp = tmp.replace('\\\\', '\\')
        return tmp
    return __php_namespace

class Options(object):
    def __init__(self, dict_in):
        dict_in = {k: Options(v) if isinstance(v, dict) else v for k, v in dict_in.items()}
        self.__dict__.update(dict_in)

    def __str__(self):
        return str({k: str(v) for k, v in self.__dict__.items()})

    def __repr__(self):
        options_props = props(self)
        props_as_attrs = ' '.join(['{}={}'.format(key, value) for key, value in options_props.items()])
        return '<Options {}>'.format(props_as_attrs)

def save_file(path, filename, filestr):
    if not os.path.isdir(path):
        os.makedirs(path)

    with open(os.path.join(path, filename), 'w') as wf:
        wf.write(filestr.encode('utf-8'))

def path_join(*p_list):
    if len(p_list)==1 and isinstance(p_list[0], (list, tuple, set)):
        p_list = p_list[0]
    return os.path.join(*p_list) if len(p_list) > 1 else (p_list[0] if p_list else '')

def merge_default(dict_in, dict_default, filter_func=None):
    [dict_in.setdefault(k, v) \
        for (k, v) in dict_default.items() \
            if filter_func is None or filter_func(k, v)]

def name_from_repr(obj):
    repr_str = repr(obj).strip()
    if repr_str.startswith('<') and repr_str.endswith('>'):
        repr_str = repr_str[1:-1].strip()

    repr_str = re.sub('(\s)at(\s)0x([0-9abcdef]+;?)', '', repr_str).strip()

    while repr_str.find(' ') > 0:
        repr_str = repr_str.split(' ', 1)[-1].strip()

    if repr_str.startswith('"') and repr_str.endswith('"'):
        repr_str = repr_str[1:-1].strip()
    if repr_str.startswith("'") and repr_str.endswith("'"):
        repr_str = repr_str[1:-1].strip()

    if repr_str.find('.') > 0:
        repr_str = repr_str.split('.')[-1].strip()
    if repr_str.find(',') > 0:
        repr_str = repr_str.split(',')[-1].strip()
    if repr_str.find(';') > 0:
        repr_str = repr_str.split(';')[-1].strip()
    return repr_str

def camel_to_underline(camel_format):
    '''
        驼峰命名格式转下划线命名格式
    '''
    underline_format=''
    if isinstance(camel_format, str):
        for _s_ in camel_format:
            underline_format += _s_ if _s_.islower() else '_'+_s_.lower()
    return underline_format

def underline_to_camel(underline_format):
    '''
        下划线命名格式驼峰命名格式
    '''
    camel_format = ''
    if isinstance(underline_format, str):
        for _s_ in underline_format.split('_'):
            camel_format += _s_.capitalize()
    return camel_format

class _OldClass:
    pass


class _NewClass(object):
    pass


_all_vars = set(dir(_OldClass) + dir(_NewClass))


def props(x):
    return {
        key: value for key, value in vars(x).items() if key not in _all_vars
    }
