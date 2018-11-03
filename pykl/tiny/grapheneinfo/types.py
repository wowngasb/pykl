#-*- coding: utf-8 -*-

from collections import OrderedDict
from inspect import isfunction, ismethod, isclass

import six
from sqlalchemy.inspection import inspect as sqlalchemyinspect

from sqlalchemy import Column

from sqlalchemy.orm.attributes import InstrumentedAttribute

import graphene
from graphene.types.objecttype import ObjectTypeMeta
from graphene.types.abstracttype import AbstractTypeMeta

from graphene.types.options import Options
from graphene.types.utils import merge, yank_fields_from_attrs
from graphene.utils.is_base_type import is_base_type

from .converter import convert_sqlalchemy_column, get_column_doc, is_column_nullable
from .registry import Registry, get_global_registry

from .utils import (
    get_query,
    is_mapped,
    BitMask,
    SortableField,
    HiddenField,
    InitializeField,
    EditableField,
    CustomField
)

class List(graphene.List):
    def __init__(self, cls, *args, **kwargs):
        super(List, self).__init__(BuildType(cls), *args, **kwargs)

class NonNull(graphene.NonNull):
    def __init__(self, cls, *args, **kwargs):
        super(NonNull, self).__init__(BuildType(cls), *args, **kwargs)

class Field(graphene.Field):
    def __init__(self, cls, *args, **kwargs):
        super(Field, self).__init__(BuildType(cls), *args, **kwargs)

def BuildArgument(cls, get_info = True, registry=None, **ext_fields):
    if not registry:
        registry = get_global_registry()
    assert isinstance(registry, Registry), (
        'The attribute registry in {}.Meta needs to be an'
        ' instance of Registry, received "{}".'
    ).format(name, registry)

    info = getattr(cls, 'info', None) if get_info else None
    if isinstance(info, InstrumentedAttribute):
        info = getattr(cls, '_info', None) if get_info else None

    if isinstance(info, BitMask):
        info = getattr(info, '_info', None)

    doc_str = getattr(cls, 'doc', None) if is_column(cls) else getattr(cls, '__doc__', None)

    if not info and is_column(cls):
        converted_type, converted_args = convert_sqlalchemy_column(cls, registry)
        converted_args['required'] = False
        return graphene.Argument(converted_type, **converted_args)

    if ismethod(info):
        cls.info = cls.info()
        return graphene.Argument(cls.info, description=doc_str)
    elif _is_graphql(info):
        return graphene.Argument(info, description=doc_str)
    elif _is_graphql(cls):
        return graphene.Argument(cls, description=doc_str)
    elif isfunction(cls):
        def _type():
            return graphene.Argument(cls(), description=doc_str)
        return _type

    else:
        raise ValueError('cannot buid_type with %r -> %r' % (cls, info))

def construct_fields(options):
    exclude_fields = set(options.exclude_fields)
    inspected_model = sqlalchemyinspect(options.model)

    fields = OrderedDict()

    for name, column in inspected_model.columns.items():
        info = getattr(column, 'info', None)
        if isinstance(info, BitMask):
            if info.has(HiddenField):
                exclude_fields.add(name)
            info = getattr(info, '_info', None)

        if _is_graphql(info):
            if hasattr(info, '_meta') and not getattr(info._meta, 'description', None):
                setattr(info._meta, 'description', get_column_doc(column))
            info = Field(info, description=get_column_doc(column), required=not(is_column_nullable(column)))
            fields[name] = info
            exclude_fields.add(name)

    for name, column in inspected_model.columns.items():
        if name in exclude_fields or name in options.fields:
            continue
        converted_type, converted_args = convert_sqlalchemy_column(column, options.registry)
        converted_column = converted_type(**converted_args)
        fields[name] = converted_column

    return fields


class SQLAlchemyObjectTypeMeta(ObjectTypeMeta):

    @staticmethod
    def __new__(cls, name, bases, attrs):
        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        if not is_base_type(bases, SQLAlchemyObjectTypeMeta):
            return type.__new__(cls, name, bases, attrs)

        meta = attrs.pop('Meta', None)
        local_fields = OrderedDict({k:v for k,v in attrs.items() if _is_graphql(v)})
        tbl_doc = attrs.pop('__doc__', getattr(meta.model, '__doc__', None))
        options = Options(
            meta,
            name=name,
            description=tbl_doc if not tbl_doc else (tbl_doc if isinstance(tbl_doc, unicode) else tbl_doc.decode('utf8')),
            model=None,
            local_fields=local_fields,
            exclude_fields=set(),
            interfaces=(),
            registry=None
        )

        if not options.registry:
            options.registry = get_global_registry()
        assert isinstance(options.registry, Registry), (
            'The attribute registry in {}.Meta needs to be an'
            ' instance of Registry, received "{}".'
        ).format(name, options.registry)
        assert is_mapped(options.model), (
            'You need to pass a valid SQLAlchemy Model in '
            '{}.Meta, received "{}".'
        ).format(name, options.model)

        cls = ObjectTypeMeta.__new__(cls, name, bases, dict(attrs, _meta=options))

        options.registry.register(cls)

        options.sqlalchemy_fields = yank_fields_from_attrs(
            construct_fields(options),
            _as = graphene.Field,
        )
        options.fields = merge(
            options.interface_fields,
            options.sqlalchemy_fields,
            options.base_fields,
            options.local_fields
        )

        return cls


class SQLAlchemyObjectType(six.with_metaclass(SQLAlchemyObjectTypeMeta, graphene.ObjectType)):

    @classmethod
    def is_type_of(cls, root, context, info):
        if isinstance(root, cls):
            return True
        if not is_mapped(type(root)):
            raise Exception((
                'Received incompatible instance "{}".'
            ).format(root))
        return isinstance(root, cls._meta.model)

    @classmethod
    def get_query(cls, context):
        model = cls._meta.model
        return get_query(model, context)

def BuildType(cls, get_info = True, base_type=SQLAlchemyObjectType, **ext_fields):
    info = getattr(cls, 'info', None) if get_info else None
    if isinstance(info, InstrumentedAttribute):
        info = getattr(cls, '_info', None) if get_info else None

    if isinstance(info, BitMask):
        info = getattr(info, '_info', None)

    if not info and is_mapped(cls):
        class Meta:
            model = cls

        cls.info = type(cls.__name__, (base_type, ), {
            '__doc__': cls.__doc__,
            'Meta': Meta,
            'name': cls.__name__
        })
        return cls.info

    if ismethod(info):
        cls.info = cls.info()
        return cls.info
    elif _is_graphql(info):
        cls.info = info
        return info
    elif _is_graphql(cls):
        return cls
    elif isfunction(cls):
        def _type():
            return BuildType(cls())
        return _type

    else:
        raise ValueError('cannot buid_type with %r -> %r' % (cls, info))


is_column = lambda cls: isinstance(cls, Column)
_is_graphql = lambda cls: isclass(cls) and issubclass(cls, (graphene.Union, graphene.Enum, graphene.Field, graphene.List, graphene.NonNull, graphene.AbstractType, graphene.Interface, graphene.InputObjectType, graphene.ObjectType, graphene.Scalar))
_is_graphql_cls = lambda cls, skip_set=set((graphene.Field, graphene.List, graphene.NonNull, Field, List, NonNull, SQLAlchemyObjectType)): _is_graphql(cls) and cls not in skip_set
_is_graphql_mutation = lambda cls: isclass(cls) and issubclass(cls, graphene.Mutation)