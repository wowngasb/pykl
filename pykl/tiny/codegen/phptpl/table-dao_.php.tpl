<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(table) %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use {{ options.base_namespace }};
use Tiny\Application;
use Tiny\OrmQuery\OrmConfig;


/**
 * Class {{ classname }}
 * {{ table.class_.__doc__ }}
 * 数据表 {{ table.class_.__tablename__ }}
 * @package {{ namespace }}
 */
class {{ classname }} extends {{ options.base_cls }}
{


    ####################################
    ########### 自动生成代码 ############
    ####################################

    /**
     * 使用这个特性的子类必须 实现这个方法 返回特定格式的数组 表示数据表的配置
     * @return OrmConfig
     */
    protected static function getOrmConfig()
    {
        $class_name = get_called_class();
        if (!isset(static::$_orm_config_map[$class_name])) {
            $db_config = Application::app()->getEnv('ENV_DB');
            $db_name = !empty($db_config['database']) ? $db_config['database'] : 'test';
            static::$_orm_config_map[$class_name] = new OrmConfig($db_name, '{{ table.class_.__tablename__ }}', '{{ table.primary_key[0].name }}', static::$cache_time, static::$max_select);
        }
        return static::$_orm_config_map[$class_name];
    }

    {%- for name, column in table.columns.items() %}
    /*
     * {{ column.type }} {{  name }} {{ column.doc if column.doc else '' }}
     */
    public static function {{ name }}(${{ table.primary_key[0].name }}, $default = null)
    {
        return static::getFiledById('{{ name }}', ${{ table.primary_key[0].name }}, $default);
    }


    {%- endfor %}
}