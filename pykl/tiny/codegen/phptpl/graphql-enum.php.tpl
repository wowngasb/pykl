<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(enum.name) %}
{%- set description = enum.description %}
{%- set description = description if description else classname %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use GraphQL\Type\Definition\EnumType;

/**
 * Class {{ classname }}
 * {{ description }}
 * @package {{ namespace }}
 */
class {{ classname }} extends EnumType
{

    {%- for name, value in enum._name_lookup.items() %}
    const {{ name }}_ENUM = {{ json.dumps(name, ensure_ascii=Flase) }};
    const {{ name }}_VALUE = {{ json.dumps(value.value, ensure_ascii=Flase) }};
    {%- endfor %}

    const ALL_ENUM_TYPE = {{ json.dumps(enum._name_lookup.keys(), ensure_ascii=Flase) }};
    const ALL_ENUM_VALUE = {{ json.dumps(map_value(enum._name_lookup.values()), ensure_ascii=Flase) }};
    const ALL_ENUM_MAP = {{ php_dict(map_enum(enum._name_lookup)) }};
        
    public function __construct(array $_config = [])
    {
        $config = [
            'description' => {{ json.dumps(description, ensure_ascii=Flase) }},
            'values' => []
        ];
        
        {%- for name, value in enum._name_lookup.items() %}
        $config['values']['{{ name }}'] = [
            'value' => '{{ value.value }}',
            {%- if description %}
            'description' => {{ json.dumps(description, ensure_ascii=Flase) }},
            {%- endif %}
        ];
        {%- endfor %}
        
        if (!empty($_config['values'])) {
            $config['values'] = array_merge($config['values'], $_config['values']);
        }
        parent::__construct($config);
    }

}