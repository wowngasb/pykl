<?php
{%- set namespace = options.namespace(options.path) %}
{%- set types_namespace = options.namespace('Types') %}
{%- set classname = options.classname(union.name) %}
{%- set description = union.description %}
{%- set description = description if description else classname %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use {{ types_namespace }};
use GraphQL\Type\Definition\ResolveInfo;
use GraphQL\Type\Definition\UnionType;

/**
 * Class {{ classname }}
 * {{ description }}
 * @package {{ namespace }}
 */
class {{ classname }} extends UnionType
{

    public function __construct(array $_config = [], $type = null)
    {
        if (is_null($type)) {
            /** @var Types $type */
            $type = Types::class;
        }
        $config = [
            'types' => [
            {%- for value in union.types %}
                $type::{{ value.name }}([], $type),
            {%- endfor %}
            ],
            'resolveType' => function ($rootValue, $context, ResolveInfo $info) use ($type) {
                false && func_get_args();
                {%- for tk, tv in union.graphene_type._type_key[1].items() %}
                {{ 'if' if loop.first else '} else if' }} ($rootValue['{{ union.graphene_type._type_key[0] }}'] == '{{ tk }}') {
                    return $type::{{ options.classname(tv) }}([], $type);
                {{- '}' if loop.last else '' }}
                {%- endfor %}
                return null;
            },
            'description' => {{ json.dumps(description, ensure_ascii=Flase) }}
        ];

        $config = array_merge($config, $_config);
        parent::__construct($config);
    }

}