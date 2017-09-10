<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(table) %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

use {{ namespace + '_\\' + classname + '_' }};


/**
 * Class {{ classname }}
 * {{ table.class_.__doc__ }}
 * 数据表 {{ table.class_.__tablename__ }}
 * @package {{ namespace }}
 */
class {{ classname }} extends {{ classname + '_' }}
{


    ####################################
    ########### 改写代码 ############
    ####################################
    
}