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
    _php_namespace,
)

from pykl.tiny.grapheneinfo.utils import (
    BitMask,
    HiddenField,
    InitializeField,
    EditableField,
    SortableField,
    CustomField,
    upper_tuple,
    mask_field,
    mask_keys,
)

class BaseBuild(object):

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

class BuildAliApi(BaseBuild):

    def __init__(self, config, options={}):
        self.config, self.options = config, Options(options)

tansMap = {
    'x-oss-acl': 'xOssAcl',
    'encoding-type': 'encodingType',
    'max-keys': 'maxKeys',
}

def api_args(fname, params, typeMap={'String':'string', 'Integer': 'int', 'Boolean': 'bool', 'RepeaList': 'array'}):
    args = []
    for key, val in params.items():
        name = (key[0].lower() + key[1:]).replace('.', '')
        name = tansMap[name] if name in tansMap else name

        val.update({
            'key': key.replace('.', ''),
            'name': name,
            'required': val.get('required', True),
            'type': val.get('type', 'String'),
            '_type': 'int' if name == 'pageNum' or name == 'pageNumber' or name == 'pageSize' else typeMap.get(val.get('type', 'String'), 'string'),
            'cn': val.get('cn', '').replace('<br>', '    '),
            'en': val.get('en', ''),
        })
        args.append(val)

    def _rank(a):
        a_ = 10000 if a['required'] else 1000
        a_ = 302 if a['name'] == 'appName' else a_
        a_ = 301 if a['name'] == 'streamName' else a_

        a_ = 202 if a['name'] == 'startTime' else a_
        a_ = 201 if a['name'] == 'endTime' else a_

        a_ = 102 if a['name'] == 'pageNum' else a_
        a_ = 102 if a['name'] == 'pageNumber' else a_
        a_ = 101 if a['name'] == 'pageSize' else a_
        return a_

    def _cmp(a, b):
        a_, b_ = _rank(a), _rank(b)
        if a_ == b_:
            return cmp(a['name'], b['name'])

        return 1 if a_ < b_ else -1

    args.sort(cmp = _cmp)
    return args

def build_api_args(fname, params):

    def _build_args(fname, name, required, _type):

        if name == 'pageNum' or name == 'pageNumber':
            return '$' + name + ' = 1'
        if name == 'pageSize':
            return '$' + name + ' = 100'
        if fname.startswith('Describe'):
            if name == 'startTime' or name == 'endTime':
                return '$' + name + ' = \'\''

        if not required:
            if name == 'appName' or name == 'streamName' or _type == 'string':
                return '$' + name + ' = \'\''
            if _type == 'int':
                return '$' + name + ' = 0'
            if _type == 'bool':
                return '$' + name + ' = null'

        return '$' + name

    pl = [_build_args(fname, p['name'], p['required'], p['_type']) for p in params]
    return ", ".join(pl)

def need_util(tag, api):
    api = api.get('api', {})
    for k, v in api.items():
        params = v.get('params', {})
        if k.startswith('Describe'):
            if 'StartTime' in params or 'EndTime' in params:
                return True

    return False

def default_utc_date(date_str, doc_str):
    if 'YYYY-MM-DDThh:mmZ' in doc_str:
        return """date('%s'), '%s'""" % (date_str, 'Y-m-d\TH:i\Z')
    else:
        return """date('%s')""" % (date_str, )

class BuildAliApiPHP(BuildAliApi):

    default_options = dict(
        file_ext = '.php',
        tpl_path = 'phptpl',
        path = 'AliApi',
        tpl = 'ali-api.tpl',
        namespace = _php_namespace('app\\api', lambda p: p),
        classname = lambda api: 'AliApi' + (api['name'].replace('-kvstore', 'KVStore') if api['name'].endswith('-kvstore') else api['name']),
        help_url = lambda tag, fname: 'http://help.aliyun.com/api/%s/%s.html' % (tag.lower(), fname),
        base_namespace = 'app\\api\\Abstracts\\BaseAliApi',
        base_request = 'BaseRpcAcsRequest',
        base_request_namespace = 'app\\api\\Abstracts\\BaseRpcAcsRequest',
        base_cls = 'BaseAliApi',
        api_args = api_args,
        need_util = need_util,
        default_utc_date = default_utc_date,
        build_api_args = build_api_args,
    )

    def __init__(self, config, **options):
        self.default_options.setdefault('_this', self)
        self.default_options.setdefault('output', None)

        merge_default(options, self.default_options)

        super(BuildAliApiPHP, self).__init__(config, options)


    def build(self):
        self._build_api(self.config, self.options)

        return True

    def _build_api(self, config, options):
        for _tag, api in config.items():
            file_name = options.classname(api) + '.php'
            tag = _tag.replace('-', '_')
            ver = api.get('version', '')
            self.render(options, file_name, _tag = _tag, tag = tag, ver = ver, api = api)

class Build(BaseBuild):
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

    def typeFromField(self, field, attach=None, args=None):
        attach = [] if attach is None else attach

        if not isinstance(field, (graphql.type.GraphQLField, graphql.type.GraphQLInputObjectField, graphql.type.GraphQLNonNull, graphql.type.GraphQLList)):
            return (field, attach, args, _is_simple(field))

        _type = field.type if isinstance(field, (graphql.type.GraphQLField, graphql.type.GraphQLInputObjectField)) and hasattr(field, 'type') else field
        _args = field.args if isinstance(field, (graphql.type.GraphQLField, )) and hasattr(field, 'args') else args

        if isinstance(_type, graphql.type.GraphQLNonNull):
            attach.append('NonNull')
            return self.typeFromField(_type.of_type, attach, _args)
        if isinstance(_type, graphql.type.GraphQLList):
            attach.append('List')
            return self.typeFromField(_type.of_type, attach, _args)

        return (_type, attach, _args, _is_simple(_type))

    def isInputType(self, val):
        return isinstance(val, graphql.type.GraphQLInputObjectType)

    def tryGetTableByType(self, val, tables):
        tmap = {name_from_repr(i) : i for i in tables}
        tname = val.name
        table = tmap.get(tname, None)
        return sqlalchemyinspect(table) if table else None

    def isColumnsFillable(self, column):
        return self.testTableColumns(column, InitializeField) or self.testTableColumns(column, EditableField)

    def isColumnsHidden(self, column):
        return self.testTableColumns(column, HiddenField)

    def isColumnsSortable(self, column):
        return self.testTableColumns(column, SortableField)

    def isTableHasColumn(self, table, column):
        return table.columns.has_key(column)

    def testTableColumns(self, column, bit_mask):
        info = getattr(column, 'info', None)
        if isinstance(info, BitMask):
            if info.has(bit_mask):
                return True

        return False

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
            base_namespace = 'app\\Dao',
            base_cls = 'Dao',
        ),
        dao = dict(
            path = 'Dao',
            namespace = _php_namespace('app\\api\\Dao', lambda p: p.replace('Dao', '')),
            classname = lambda t: name_from_repr(t) + 'Dao',
            tpl = 'table-dao.php.tpl',
        ),
        model = dict(
            path = 'Model',
            namespace = _php_namespace('app\\Model', lambda p: p.replace('Model', '')),
            classname = lambda t: name_from_repr(t),
            tpl = 'table-model.php.tpl',
        ),
        model_ = dict(
            path = 'Model_',
            namespace = _php_namespace('app\\Model_', lambda p: p.replace('Model_', '')),
            classname = lambda t: name_from_repr(t),
            tpl = 'table-model_.php.tpl',
            base_type_path = 'app\\api\\GraphQL_\\Type',
            base_model_path = 'app',
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
        for tag in ('dao', 'dao_', 'graphql', 'model', 'model_'):
            tmp_dict = dict(self.default_options[tag])
            tmp_dict.update(options[tag])
            options[tag] = tmp_dict
            options[tag].setdefault('path', '')

            options[tag]['path'] = path_join([p for p in (options['path'], options[tag]['path']) if p])
            merge_default(options[tag], options, lambda k,v: not isinstance(v, dict))

        for tag in ('enum', 'type', 'exttype', 'abstracttype', 'union', 'query', 'types'):
            tmp_dict = dict(self.default_options['graphql'][tag])
            tmp_dict.update(options['graphql'][tag])
            options['graphql'][tag] = tmp_dict
            options['graphql'][tag].setdefault('path', '')

            options['graphql'][tag]['path'] = path_join([p for p in (options['graphql']['path'], options['graphql'][tag]['path']) if p])
            merge_default(options['graphql'][tag], options['graphql'], lambda k,v: not isinstance(v, dict))

        super(BuildPHP, self).__init__(schema, tables, options)
        self.class_map = OrderedDict()

    def build(self):
        self._build_type(self.options.graphql.type, self.types, self.tables)

        self._build_query(self.options.graphql.query, self.query)
        self._build_exttype(self.options.graphql.exttype, self.exttypes)
        self._build_enum(self.options.graphql.enum, self.enums)
        self._build_union(self.options.graphql.union, self.unions)

        self._build_abstracttype(self.options.graphql.abstracttype, self.abstracttypes, self.class_map)
        self._build_types(self.options.graphql.types, self.query, self.abstracttypes, self.types, self.exttypes, self.enums, self.unions, self.class_map)

        self._build_dao_(self.options.dao_, self.tables)
        self._build_dao(self.options.dao, self.tables)
        self._build_model(self.options.model, self.tables)
        self._build_model_(self.options.model_, self.tables)
        return True

    def _build_types(self, options, query, abstracttypes, types, exttypes, enums, unions, class_map):
        classname = 'Types'
        file_name = options.classname(classname) + options.file_ext

        abstract_types = {n: t for n, t in types.items() if n in abstracttypes}
        table_types = {n: t for n, t in types.items() if n not in abstracttypes}

        self.render(
            options,
            file_name,
            query = query,
            types = types,
            abstract_types = abstract_types,
            table_types = table_types,
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

    def _build_type(self, options, types, tables):
        for classname, type in types.items():
            file_name = options.classname(classname) + options.file_ext
            self.render(options, file_name, type = type, tables = tables)
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

    def _build_model(self, options, tables):
        for _table in tables:
            table = sqlalchemyinspect(_table)
            file_name = options.classname(table) + options.file_ext
            self.render(options, file_name, table = table)

    def _build_model_(self, options, tables):
        for _table in tables:
            table = sqlalchemyinspect(_table)
            file_name = options.classname(table) + '_' + options.file_ext
            self.render(options, file_name, table = table)

    def buildDefaultByType(self, atype):
        if atype.endswith('Range'):
            atype = 'Range'
        if atype.endswith('Enum'):
            atype = 'Enum'
        if atype.endswith('SortOption'):
            atype = 'Option'

        dmap = {
            'String': "''",
            'Int': "0",
            'Float': "0.0",
            'Bool': "false",
            'Range': "[]",
            'Option': "[]",
            'Enum': "'UNKNOWN'",
        }
        return dmap.get(atype, "''")

    def buildValueByType(self, atype, val):
        if atype.endswith('Range'):
            atype = 'Range'
        if atype.endswith('Enum'):
            atype = 'Enum'
        if atype.endswith('SortOption'):
            atype = 'Option'

        dmap = {
            'String': "strval(%s)",
            'Int': "intval(%s)",
            'Float': "floatval(%s)",
            'Bool': "boolval(%s)",
            'Range': "(array)%s",
            'Option': "(array)%s",
            'Enum': "%s",
        }
        return dmap.get(atype, "%s") % (val, )

    def buildTypeByColumn(self, column):
        atype = str(column.type)
        if atype.startswith('VARCHAR'):
            atype = 'VARCHAR'
        if atype.startswith('CHAR'):
            atype = 'CHAR'

        dmap = {
            'INTEGER': "int",
            'MEDIUMINT':"int",
            'CHAR': "string",
            'VARCHAR': "string",
            'SMALLINT': "int",
            'TIMESTAMP': "string",
            'DATETIME': "string",
            'BOOL': 'bool',
            'DOUBLE': 'float',
            'FLOAT': 'float',
        }
        return dmap.get(atype, "string")

    def buildValueByColumn(self, column, val):
        atype = str(column.type)
        if atype.startswith('VARCHAR'):
            atype = 'VARCHAR'
        if atype.startswith('CHAR'):
            atype = 'CHAR'

        dmap = {
            'INTEGER': "intval(%s)",
            'MEDIUMINT':"intval(%s)",
            'CHAR': "strval(%s)",
            'VARCHAR': "strval(%s)",
            'SMALLINT': "intval(%s)",
            'TIMESTAMP': "strval(%s)",
            'DATETIME': "strval(%s)",
            'BOOL': 'boolval(%s)',
            'DOUBLE': 'floatval(%s)',
            'FLOAT': 'floatval(%s)',
        }
        return dmap.get(atype, "%s") % (val, )

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
