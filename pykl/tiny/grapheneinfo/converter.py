#-*- coding: utf-8 -*-

from singledispatch import singledispatch
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import interfaces

from graphene import (ID, Boolean, Enum, Field, Float, Int, List,
                      String)


def get_column_doc(column):
    return getattr(column, 'doc', None)


def is_column_nullable(column):
    return bool(getattr(column, 'nullable', False))



def convert_sqlalchemy_column(column, registry=None):
    return convert_sqlalchemy_type(getattr(column, 'type', None), column, registry)


def get_column_args(column):
    return dict(description=get_column_doc(column), required=not (is_column_nullable(column)))

@singledispatch
def convert_sqlalchemy_type(type, column, registry=None):
    raise Exception(
        "Don't know how to convert the SQLAlchemy field %s (%s)" % (column, column.__class__))


@convert_sqlalchemy_type.register(types.Date)
@convert_sqlalchemy_type.register(types.Time)
@convert_sqlalchemy_type.register(types.DateTime)
@convert_sqlalchemy_type.register(types.String)
@convert_sqlalchemy_type.register(types.Text)
@convert_sqlalchemy_type.register(types.Unicode)
@convert_sqlalchemy_type.register(types.UnicodeText)
@convert_sqlalchemy_type.register(types.Enum)
@convert_sqlalchemy_type.register(postgresql.ENUM)
@convert_sqlalchemy_type.register(postgresql.UUID)
def convert_column_to_string(type, column, registry=None):
    return String, dict(description=get_column_doc(column),
                  required=not(is_column_nullable(column)))


@convert_sqlalchemy_type.register(types.SmallInteger)
@convert_sqlalchemy_type.register(types.Integer)
def convert_column_to_int_or_id(type, column, registry=None):
    if column.primary_key:
        return Int, get_column_args(column)
    else:
        return Int, get_column_args(column)


@convert_sqlalchemy_type.register(types.Boolean)
def convert_column_to_boolean(type, column, registry=None):
    return Boolean, get_column_args(column)


@convert_sqlalchemy_type.register(types.Float)
@convert_sqlalchemy_type.register(types.Numeric)
@convert_sqlalchemy_type.register(types.BigInteger)
def convert_column_to_float(type, column, registry=None):
    return Float, get_column_args(column)
