<?php
{%- set namespace = options.namespace(options.path) %}
{%- set types_namespace = options.namespace('Types') %}
{%- set classname = options.classname(type.name) %}
{%- set description = type.description %}
{%- set description = description if description else classname %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use {{ types_namespace }};
use GraphQL\Type\Definition\ObjectType;
use GraphQL\Type\Definition\ResolveInfo;

{%- macro render_filed_type(_type, attach, register_t_args) -%}
    {%- if len(attach)==1 and (attach[0]=='List' or attach[0]=='NonNull') -%}
        $type::{{ 'listOf' if attach[0]=='List' else 'nonNull' }}($type::{{ _type.name }}({{ register_t_args }}))
    {%- elif len(attach)==2 and (attach[0]=='List' or attach[0]=='NonNull') and (attach[1]=='List' or attach[1]=='NonNull') -%}
        $type::{{ 'listOf' if attach[0]=='List' else 'nonNull' }}($type::{{ 'listOf' if attach[1]=='List' else 'nonNull' }}($type::{{ _type.name }}({{ register_t_args }})))
    {%- else -%}
        $type::{{ _type.name }}({{ register_t_args }})
    {%- endif %}
{%- endmacro -%}

/**
 * Class {{ classname }}
 * {{ description }}
 * @package {{ namespace }}
 */
class {{ classname }} extends ObjectType
{

    public function __construct(array $_config = [], $type = null)
    {
        if (is_null($type)) {
            /** @var Types $type */
            $type = Types::class;
        }

        $_description = !empty($_config['description']) ? $_config['description'] : {{ json.dumps(description, ensure_ascii=Flase) }};
        $_fields = !empty($_config['fields']) ? $_config['fields'] : [];
        
        $config = [
            'description' => $_description,
            'fields' => function () use ($type, $_fields) {
                $fields = [];
                {%- for name, value in type.fields.items() %}
                {%- set f_type, f_attach, f_args, f_is_simple_type = options._this.typeFromField(value) %}
                {%- set f_register_type_args = '' if f_is_simple_type else '[], $type' %}
                $fields['{{ name }}'] = [
                    'type' => {{ render_filed_type(f_type, f_attach, f_register_type_args) }},
                    {%- if value.description %}
                    'description' => {{ json.dumps(value.description, ensure_ascii=Flase) }},
                    {%- endif %}
                    {%- if value.deprecation_reason %}
                     'deprecationReason' => {{ json.dumps(value.deprecation_reason, ensure_ascii=Flase) }},
                     {%- endif %}
                    {%- if f_args %}
                    'args' => [
                        {%- for a_key, a_val in f_args.items() %}
                        '{{ a_key }}' => [
                            {%- set a_type, a_attach, a_has_default, a_is_simple_type = options._this.typeFromArgument(a_val) %}
                            {%- set a_register_type_args = '' if a_is_simple_type else '[], $type' %}
                            'type' => {{ render_filed_type(a_type, a_attach, a_register_type_args) }},
                            {%- if a_val.description %}
                            'description' => {{ json.dumps(a_val.description, ensure_ascii=Flase) }},
                            {%- endif %}
                            {%- if a_has_default %}
                            'defaultValue' => {{ json.dumps(a_val.default_value, ensure_ascii=Flase) }},
                            {%- endif %}
                        ],
                        {%- endfor %}
                    ],
                    {%- endif %}
                ];
                {%- endfor %}
                return array_merge($fields, $_fields);
            },
            'resolveField' => function($value, $args, $context, ResolveInfo $info) {
                if (method_exists($this, $info->fieldName)) {
                    return $this->{$info->fieldName}($value, $args, $context, $info);
                } else {
                    return is_array($value) ? $value[$info->fieldName] : $value->{$info->fieldName};
                }
            },
        ];
        parent::__construct($config);
    }

}