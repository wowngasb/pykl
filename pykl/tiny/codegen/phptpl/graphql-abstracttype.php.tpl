<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(abstracttype.name) %}
{%- set description = abstracttype.description %}
{%- set description = description if description else classname %}
{%- set parent_options = _class_map[_classname][0] %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use {{ parent_options.namespace(parent_options.path) }}\{{ _classname }};

use GraphQL\Type\Definition\ResolveInfo;

/**
 * Class {{ classname }}
 * {{ description }}
 * @package {{ namespace }}
 */
abstract class {{ classname }} extends {{ _classname }}
{

    {%- for f_name, _ in abstracttype.graphene_type._meta.local_fields.items() %}
    {%- if f_name not in ('hello', 'deprecatedField', 'fieldWithException') %}
    {%- set f_value = abstracttype.fields[f_name] %}
    
    /**
     * {{ f_value.description }}
    {%- set f_type, f_attach, f_args, f_is_simple_type = options._this.typeFromField(f_value) %}
    {%- if f_args %}
    {%- for a_key, a_val in f_args.items() %}
    {%- set a_type, a_attach, a_has_default, a_is_simple_type = options._this.typeFromArgument(a_val) %}
     * _param {{ a_type.name }} $args['{{ a_key }}']{{ ' = ' + json.dumps(a_val.default_value, ensure_ascii=Flase) if a_has_default else '' }} {{ a_val.description }} {{ '(' + ','.join(a_attach) + ')' if a_attach else '' }}
    {%- endfor %}
    {%- endif %}
     * ---------------------
     * @param array $rootValue
     * @param array $args
     * @param mixed $context
     * @param ResolveInfo $info
     * @return mixed {{ f_type.name }}
     */
    abstract public function {{ f_name }}($rootValue, $args, $context, ResolveInfo $info);
    {%- endif %}
    {%- endfor %}
    
}