#-*- coding: utf-8 -*-
import os
from collections import OrderedDict

import graphql

from sqlalchemy.inspection import inspect as sqlalchemyinspect

from .utils import (
    Options,
    camel_to_underline,
    underline_to_camel,
    name_from_repr,
    merge_default,
    save_file,
    path_join,
    render_template_file,
    _is_base,
    _is_enum,
    _is_union,
    _is_sqlalchemy,
    _is_abstract_sqlalchemy,
    _is_simple,
    _php_namespace
)


class Build(object):
    _graphiql_query = '''
query IntrospectionQuery { __schema { queryType { name } mutationType { name } subscriptionType { name } types { ...FullType } directives { name description locations args { ...InputValue } } } } fragment FullType on __Type { kind name description fields(includeDeprecated: true) { name description args { ...InputValue } type { ...TypeRef } isDeprecated deprecationReason } inputFields { ...InputValue } interfaces { ...TypeRef } enumValues(includeDeprecated: true) { name description isDeprecated deprecationReason } possibleTypes { ...TypeRef } } fragment InputValue on __InputValue { name description type { ...TypeRef } defaultValue } fragment TypeRef on __Type { kind name ofType { kind name ofType { kind name ofType { kind name } } } }
    '''

    def __init__(self, schema, tables, options={}):
        self.schema, self.tables, self.options = schema, tables, Options(options)

        self.info = schema.execute(self._graphiql_query)
        self._types = {k:v for k, v in schema._type_map.items() if not _is_base(v) and not k.startswith('__')}
        self.query = self._types.get('Query', None)
        self.enums = {k:v for k, v in self._types.items() if _is_enum(v)}
        self.unions = {k:v for k, v in self._types.items() if _is_union(v)}
        [setattr(union, 'description', union.graphene_type._meta.description) for union in self.unions.values()]

        self.types = {k:v for k, v in self._types.items() if _is_sqlalchemy(v)}
        self.abstracttypes = {k:v for k, v in self._types.items() if _is_abstract_sqlalchemy(v)}
        self.abstracttypes.setdefault('Query', self.query)

        key_map = set(['Query'] + self.enums.keys() + self.unions.keys() + self.types.keys())
        self.exttypes = {k:v for k, v in self._types.items() if k not in key_map}


        '''
        print 'data:', self.info.data
        print 'errors:', self.info.errors
        print self.types
        print self.query
        '''

    def build(self):
        return False

    def dump(self, options, file_name, file_str):
        if options.output:
            outpath = os.path.join(options.output, options.path)
            save_file(outpath, file_name, file_str)
            print 'save file', os.path.join(outpath, file_name)
        else:
            print "\n", '/* >>>>>>>> ', os.path.join(options.path, file_name), ' <<<<<<<< */', "\n"
            print file_str

    def render(self, options, file_name, **context):
        file_str = render_template_file(
            options.tpl_path,
            options.tpl,
            options = options,
            **context
        )
        self.dump(options, file_name, file_str)

    def typeFromField(self, field, attach=None, args=None):
        attach = [] if attach is None else attach

        if not isinstance(field, (graphql.type.GraphQLField, graphql.type.GraphQLNonNull, graphql.type.GraphQLList)):
            return (field, attach, args, _is_simple(field))

        _type = field.type if isinstance(field, (graphql.type.GraphQLField,)) else field
        _args = field.args if isinstance(field, (graphql.type.GraphQLField,)) else args

        if isinstance(_type, graphql.type.GraphQLNonNull):
            attach.append('NonNull')
            return self.typeFromField(_type.of_type, attach, _args)
        if isinstance(_type, graphql.type.GraphQLList):
            attach.append('List')
            return self.typeFromField(_type.of_type, attach, _args)

        return (_type, attach, _args, _is_simple(_type))

    def typeFromArgument(self, field, attach=None, has_default=False):
        attach = [] if attach is None else attach

        if not isinstance(field, (graphql.type.GraphQLArgument, graphql.type.GraphQLNonNull, graphql.type.GraphQLList)):
            return (field, attach, has_default, _is_simple(field))

        _type = field.type if isinstance(field, (graphql.type.GraphQLArgument,)) else field
        _has_default = not field.default_value is None if isinstance(field, (graphql.type.GraphQLArgument,)) else has_default

        if isinstance(_type, graphql.type.GraphQLNonNull):
            attach.append('NonNull')
            return self.typeFromArgument(_type.of_type, attach, _has_default)
        if isinstance(_type, graphql.type.GraphQLList):
            attach.append('List')
            return self.typeFromArgument(_type.of_type, attach, _has_default)

        return (_type, attach, _has_default, _is_simple(_type))

class BuildPHP(Build):
    default_options = dict(
        file_ext = '.php',
        tpl_path = 'phptpl',
        classname = lambda t: name_from_repr(t),
        dao_ = dict(
            path = 'Dao_',
            namespace = _php_namespace('app\\api\\Dao_', lambda p: p.replace('Dao_', '')),
            classname = lambda t: name_from_repr(t) + 'Dao_',
            tpl = 'table-dao_.php.tpl',
            base_namespace = 'app\\api\\base\\BaseDao',
            base_cls = 'BaseDao',
        ),
        dao = dict(
            path = 'Dao',
            namespace = _php_namespace('app\\api\\Dao', lambda p: p.replace('Dao', '')),
            classname = lambda t: name_from_repr(t) + 'Dao',
            tpl = 'table-dao.php.tpl',
        ),
        graphql = dict(
            path = 'GraphQL_',
            namespace = _php_namespace('app\\api\\GraphQL_', lambda p: p.replace('GraphQL_', '')),
            enum = dict(
                path = 'Enum',
                tpl = 'graphql-enum.php.tpl',
            ),
            type = dict(
                path = 'Type',
                tpl = 'graphql-type.php.tpl',
            ),
            exttype = dict(
                path = 'ExtType',
                tpl = 'graphql-type.php.tpl',
            ),
            union = dict(
                path = 'Union',
                tpl = 'graphql-union.php.tpl',
            ),
            abstracttype = dict(
                classname = lambda t: 'Abstract' + name_from_repr(t),
                tpl = 'graphql-abstracttype.php.tpl',
            ),
            query = dict(
                path = 'ExtType',
                tpl = 'graphql-query.php.tpl',
            ),
            types = dict(
                tpl = 'graphql-types.php.tpl',
            ),
        )
    )

    def __init__(self, schema, tables, **options):
        self.default_options.setdefault('_this', self)
        self.default_options.setdefault('path', '')
        self.default_options.setdefault('output', None)

        merge_default(options, self.default_options)
        for tag in ('dao', 'dao_', 'graphql'):
            options[tag].setdefault('path', '')
            options[tag]['path'] = path_join([p for p in (options['path'], options[tag]['path']) if p])
            merge_default(options[tag], options, lambda k,v: not isinstance(v, dict))

        for tag in ('enum', 'type', 'exttype', 'abstracttype', 'union', 'query', 'types'):
            options['graphql'][tag].setdefault('path', '')
            options['graphql'][tag]['path'] = path_join([p for p in (options['graphql']['path'], options['graphql'][tag]['path']) if p])
            merge_default(options['graphql'][tag], options['graphql'], lambda k,v: not isinstance(v, dict))

        super(BuildPHP, self).__init__(schema, tables, options)
        self.class_map = OrderedDict()

    def build(self):

        self._build_query(self.options.graphql.query, self.query)
        self._build_type(self.options.graphql.type, self.types)
        self._build_exttype(self.options.graphql.exttype, self.exttypes)
        self._build_enum(self.options.graphql.enum, self.enums)
        self._build_union(self.options.graphql.union, self.unions)

        self._build_abstracttype(self.options.graphql.abstracttype, self.abstracttypes, self.class_map)
        self._build_types(self.options.graphql.types, self.query, self.types, self.exttypes, self.enums, self.unions, self.class_map)

        self._build_dao_(self.options.dao_, self.tables)
        self._build_dao(self.options.dao, self.tables)
        return True

    def _build_types(self, options, query, types, exttypes, enums, unions, class_map):
        classname = 'Types'
        file_name = options.classname(classname) + options.file_ext
        self.render(
            options,
            file_name,
            query = query,
            types = types,
            exttypes = exttypes,
            enums = enums,
            unions = unions,
            _class_map = class_map,
            _classname = classname,
        )

    def _build_query(self, options, query):
        classname = 'Query'
        file_name = options.classname(classname) + options.file_ext
        self.render(options, file_name, query = query)
        self.class_map.setdefault(classname, (options, query))

    def _build_type(self, options, types):
        for classname, type in types.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(options, file_name, type = type)
            self.class_map.setdefault(classname, (options, type))

    def _build_exttype(self, options, exttypes):
        for classname, exttype in exttypes.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(options, file_name, type = exttype)
            self.class_map.setdefault(classname, (options, exttype))

    def _build_abstracttype(self, options, abstracttypes, class_map):
        for classname, abstracttype in abstracttypes.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(
                options,
                file_name,
                abstracttype = abstracttype,
                _class_map = class_map,
                _classname = classname,
            )

    def _build_enum(self, options, enums):
        for classname, enum in enums.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(options, file_name, enum = enum)
            self.class_map.setdefault(classname, (options, enum))

    def _build_union(self, options, unions):
        for classname, union in unions.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(options, file_name, union = union)
            self.class_map.setdefault(classname, (options, union))

    def _build_dao_(self, options, tables):
        for _table in tables:
            table = sqlalchemyinspect(_table)
            file_name = options.classname(table) + options.file_ext
            self.render(options, file_name, table = table)

    def _build_dao(self, options, tables):
        for _table in tables:
            table = sqlalchemyinspect(_table)
            file_name = options.classname(table) + options.file_ext
            self.render(options, file_name, table = table)

class BuildGO(Build):
    default_options = dict()

    def __init__(self, schema, tables, **options):
        [options.setdefault(k, v) for (k, v) in self.default_options.items()]
        super(BuildGO, self).__init__(schema, tables, options)

class BuildJAVA(Build):
    default_options = dict()

    def __init__(self, schema, tables, **options):
        [options.setdefault(k, v) for (k, v) in self.default_options.items()]
        super(BuildJAVA, self).__init__(schema, tables, options)
