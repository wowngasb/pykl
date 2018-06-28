<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = _classname %}
{%- set class_map = _class_map %}
{%- set description = 'Acts as a registry and factory for types.' %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

//import query classes
use {{ class_map[ query.name ][0].namespace( class_map[ query.name ][0].path + '\\' + query.name ) }};

//import Type tables classes

{%- for t, v in types.items() %}
use {{ class_map[ t ][0].namespace( class_map[t][0].path + '\\' + t ) }};
{%- endfor %}

//import Type exttypes classes

{%- for t, v in exttypes.items() %}
use {{ class_map[ t ][0].namespace( class_map[t][0].path + '\\' + t ) }};
{%- endfor %}

//import Type enums classes

{%- for t, v in enums.items() %}
use {{ class_map[ t ][0].namespace( class_map[t][0].path + '\\' + t ) }};
{%- endfor %}

//import Type unions classes

{%- for t, v in unions.items() %}
use {{ class_map[ t ][0].namespace( class_map[t][0].path + '\\' + t ) }};
{%- endfor %}


//import Type Definition classes
use GraphQL\Type\Definition\ListOfType;
use GraphQL\Type\Definition\NonNull;
use GraphQL\Type\Definition\Type;

/**
 * Class {{ classname }}
 * {{ description }}
 * @package {{ namespace }}
 */
class {{ classname }}
{

    ####################################
    ########  root query type  #########
    ####################################

    private static $_m{{ query.name }} = null;

    /**
     * 必须实现 Abstract{{ query.name }} 中的虚方法 才可以使用完整的查询 此方法需要重写
     * @param array $config
     * @param mixed $type
     * @return {{ query.name }}
     */
    public static function {{ query.name }}(array $config = [], $type = null)
    {
        return self::$_m{{ query.name }} ?: (self::$_m{{ query.name }} = new {{ query.name }}($config, $type));
    }

    ####################################
    ##########  abstract types  ##########
    ####################################
    
    {%- for t, v in abstract_types.items() %}

    private static $_m{{ t }} = null;

    /**
     * {{ class_map[ t ][1].description if class_map[ t ][1].description else t }}
     * @param array $config
     * @param mixed $type
     * @return {{ t }}
     */
    public static function {{ t }}(array $config = [], $type = null)
    {
        return self::$_m{{ t }} ?: (self::$_m{{ t }} = new {{ t }}($config, $type));
    }

    {%- endfor %}

    ####################################
    ##########  table types  ##########
    ####################################
    
    {%- for t, v in table_types.items() %}

    private static $_m{{ t }} = null;

    /**
     * {{ class_map[ t ][1].description if class_map[ t ][1].description else t }}
     * @param array $config
     * @param mixed $type
     * @return {{ t }}
     */
    public static function {{ t }}(array $config = [], $type = null)
    {
        return self::$_m{{ t }} ?: (self::$_m{{ t }} = new {{ t }}($config, $type));
    }

    {%- endfor %}

    ####################################
    ######### exttypes types #########
    ####################################

    {%- for t, v in exttypes.items() %}

    private static $_m{{ t }} = null;

    /**
     * {{ class_map[ t ][1].description if class_map[ t ][1].description else t }}
     * @param array $config
     * @param mixed $type
     * @return {{ t }}
     */
    public static function {{ t }}(array $config = [], $type = null)
    {
        return self::$_m{{ t }} ?: (self::$_m{{ t }} = new {{ t }}($config, $type));
    }

    {%- endfor %}


    ####################################
    ######### enums types #########
    ####################################

    {%- for t, v in enums.items() %}

    private static $_m{{ t }} = null;

    /**
     * {{ class_map[ t ][1].description if class_map[ t ][1].description else t }}
     * @param array $config
     * @return {{ t }}
     */
    public static function {{ t }}(array $config = [])
    {
        return self::$_m{{ t }} ?: (self::$_m{{ t }} = new {{ t }}($config));
    }

    {%- endfor %}

    ####################################
    ######### unions types #########
    ####################################

    {%- for t, v in unions.items() %}

    private static $_m{{ t }} = null;

    /**
     * {{ class_map[ t ][1].description if class_map[ t ][1].description else t }}
     * @param array $config
     * @param mixed $type
     * @return {{ t }}
     */
    public static function {{ t }}(array $config = [], $type = null)
    {
        return self::$_m{{ t }} ?: (self::$_m{{ t }} = new {{ t }}($config, $type));
    }

    {%- endfor %}

    ####################################
    ########## internal types ##########
    ####################################

    public static function boolean()
    {
        return Type::boolean();
    }

    /**
     * @return \GraphQL\Type\Definition\FloatType
     */
    public static function float()
    {
        return Type::float();
    }

    /**
     * @return \GraphQL\Type\Definition\IDType
     */
    public static function id()
    {
        return Type::id();
    }

    /**
     * @return \GraphQL\Type\Definition\IntType
     */
    public static function int()
    {
        return Type::int();
    }

    /**
     * @return \GraphQL\Type\Definition\StringType
     */
    public static function string()
    {
        return Type::string();
    }

    /**
     * @param Type $type
     * @return ListOfType
     */
    public static function listOf($type)
    {
        return new ListOfType($type);
    }

    /**
     * @param Type $type
     * @return NonNull
     */
    public static function nonNull($type)
    {
        return new NonNull($type);
    }
}