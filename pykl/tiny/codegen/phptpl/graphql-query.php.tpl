<?php
{%- set namespace = options.namespace(options.path) %}
{%- set types_namespace = options.namespace('Types') %}
{%- set classname = options.classname(query.name) %}
{%- set description = query.description %}
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
        $config = [
            'description' => {{ json.dumps(description, ensure_ascii=Flase) }},
            'fields' => []
        ];

{%- macro render_filed_type(_type, attach, register_t_args) -%}
    {%- if len(attach)==1 and (attach[0]=='List' or attach[0]=='NonNull') -%}
        $type::{{ 'listOf' if attach[0]=='List' else 'nonNull' }}($type::{{ _type.name }}({{ register_t_args }}))
    {%- elif len(attach)==2 and (attach[0]=='List' or attach[0]=='NonNull') and (attach[1]=='List' or attach[1]=='NonNull') -%}
        $type::{{ 'listOf' if attach[0]=='List' else 'nonNull' }}($type::{{ 'listOf' if attach[1]=='List' else 'nonNull' }}($type::{{ _type.name }}({{ register_t_args }})))
    {%- else -%}
        $type::{{ _type.name }}({{ register_t_args }})
    {%- endif %}
{%- endmacro -%}

        {%- for name, value in query.fields.items() %}
        $config['fields']['{{ name }}'] = [
            {%- set f_type, f_attach, f_args, f_is_simple_type = options._this.typeFromField(value) %}
            {%- set f_register_type_args = '' if f_is_simple_type else '[], $type' %}
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
        
        $config['resolveField'] = function($value, $args, $context, ResolveInfo $info) {
            if (method_exists($this, $info->fieldName)) {
                return $this->{$info->fieldName}($value, $args, $context, $info);
            } else {
                return is_array($value) ? $value[$info->fieldName] : $value->{$info->fieldName};
            }
        };
        if (!empty($_config['fields'])) {
            $config['fields'] = array_merge($_config['fields'], $config['fields']);
        }
        parent::__construct($config);
    }
    
    public function hello($value, $args, $context, ResolveInfo $info)
    {
        return "Hello {$args['name']}, Your graphql-php endpoint is ready! Use GraphiQL to browse API";
    }

    public function deprecatedField()
    {
        return 'You can request deprecated field, but it is not displayed in auto-generated documentation by default.';
    }

    public function fieldWithException()
    {
        throw new \Exception("Exception message thrown in field resolver");
    }

}