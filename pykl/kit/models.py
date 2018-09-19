# coding: utf-8
import random
import time
import hashlib
from inspect import isclass

from sqlalchemy.inspection import inspect as sqlalchemyinspect
from sqlalchemy.ext.declarative import declarative_base

from pykl.tiny.grapheneinfo import (
    _is_graphql,
    _is_graphql_cls,
    _is_graphql_mutation
)

from pykl.tiny.codegen.utils import (
    name_from_repr,
    camel_to_underline,
    underline_to_camel,
)

from base_type import *
from cmd import db, app
Base = db.Model


class MigrateVersion(Base):
    u"""table migrate_version"""
    __tablename__ = 'migrate_version'

    repository_id = Column(String(191), primary_key=True, doc=u"""field repository_id""", info=CustomField | SortableField)
    repository_path = Column(Text, doc=u"""field repository_path""", info=CustomField | SortableField)
    version = Column(Integer, doc=u"""field version""", info=CustomField | SortableField)


##############################################################
###################		根查询 Query		######################
##############################################################

class Query(g.ObjectType):
    hello = g.String(name=g.Argument(g.String, default_value="world", description=u'input you name'))
    deprecatedField = Field(g.String, deprecation_reason = 'This field is deprecated!')
    fieldWithException = g.String()
    migrateVersion = Field(MigrateVersion, description=u'migrate_version')
    
    def resolve_hello(self, args, context, info):
        return 'Hello, %s!' % (args.get('name', ''), )

    def resolve_deprecatedField(self, args, context, info):
        return 'You can request deprecated field, but it is not displayed in auto-generated documentation by default.'

    def resolve_fieldWithException(self, args, context, info):
        raise ValueError('Exception message thrown in field resolver')

    def resolve_migrateVersion(self, args, context, info):
        return MigrateVersion.query.first()
        
##############################################################
###################		 Mutations		######################
##############################################################
def build_input(dao, bit_mask):
    return {k: BuildArgument(v) for k, v in mask_field(dao, bit_mask).items()}

class CreateMigrateVersion(g.Mutation):
    Input = type('Input', (), build_input(MigrateVersion, InitializeField))

    ok = g.Boolean()
    msg = g.String()
    migrateVersion = Field(MigrateVersion)

    @staticmethod
    def mutate(root, args, context, info):
        return CreateMigrateVersion(ok=True, msg='suc', migrateVersion=MigrateVersion.query.first())

class UpdateMigrateVersion(g.Mutation):
    Input = type('Input', (), build_input(MigrateVersion, EditableField))

    ok = g.Boolean()
    msg = g.String()
    migrateVersion = Field(MigrateVersion)

    @staticmethod
    def mutate(root, args, context, info):
        return UpdateMigrateVersion(ok=True, msg='suc', migrateVersion=MigrateVersion.query.first())

##############################################################
###################		根查询 Mutations		######################
##############################################################

Mutations = type('Mutations', (g.ObjectType, ), {camel_to_underline(name_from_repr(v)):v.Field() for _, v in globals().items() if _is_graphql_mutation(v)})

tables = [tbl if BuildType(tbl) else tbl for _, tbl in globals().items() if isclass(tbl) and issubclass(tbl, Base) and tbl != Base]
schema = g.Schema(query=Query, mutation=Mutations, types=[BuildType(tbl) for tbl in tables] + [cls for _, cls in globals().items() if _is_graphql_cls(cls)], auto_camelcase = False)