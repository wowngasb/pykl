<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(table) %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

{%- set base_model = 'StateModel' if options._this.isTableHasColumn(table, 'state')  else 'Model' %}

use {{ options.base_type_path }}\{{ classname }} as _{{ classname }};
use {{ options.base_model_path }}\{{ base_model }};

/**
 * Class {{ classname }}
 * {{ table.class_.__doc__ }}
 * 数据表 {{ table.class_.__tablename__ }}
 * @package {{ namespace }}
 */
class {{ classname }}_ extends {{ base_model }}
{

    const PRIMARY_KEY = _{{ classname }}::PRIMARY_KEY;
    const TABLE_NAME = _{{ classname }}::TABLE_NAME;
    const FILLABLE_FIELDS = _{{ classname }}::FILLABLE_FIELDS;
    const HIDDEN_FIELDS = _{{ classname }}::HIDDEN_FIELDS;
    const SORTABLE_FIELDS = _{{ classname }}::SORTABLE_FIELDS;
    const ALL_FIELDS = _{{ classname }}::ALL_FIELDS;

    protected $primaryKey = _{{ classname }}::PRIMARY_KEY;
    protected $table = _{{ classname }}::TABLE_NAME;
    protected $fillable = _{{ classname }}::FILLABLE_FIELDS;
    protected $hidden = _{{ classname }}::HIDDEN_FIELDS;
    protected $sortable = _{{ classname }}::SORTABLE_FIELDS;
    protected $allfields = _{{ classname }}::ALL_FIELDS;

    {%- for name, column in table.columns.items() %}
    
    /**
     * 根据主键 获取单个条目的 某个字段   自动使用缓存
     * {{ column.type }} {{  name }} {{ column.doc if column.doc else '' }}
     * @param int ${{ table.primary_key[0].name }}  条目 主键
     * @param string $default 无对应条目时的默认值
     * @param null $timeCache
     * @return {{ options._this.buildTypeByColumn(column) }}
     */
    public static function {{ name }}(${{ table.primary_key[0].name }}, $default = '', $timeCache = null)
    {
        $val = static::valueOneById(${{ table.primary_key[0].name }}, '{{ name }}', $default, $timeCache);
        return {{ options._this.buildValueByColumn(column, '$val') }};
    }
    {%- endfor %}

}