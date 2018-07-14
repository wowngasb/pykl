<?php
{%- set namespace = options.namespace(options.path) %}
{%- set classname = options.classname(api) %}
/**
 * Created by table_graphQL.
 * 用于PHP Tiny框架
 * Date: {{ time.strftime('%Y-%m') }}
 */
namespace {{ namespace }};

{% if options.need_util(tag, api) %}
use app\Util;
{% endif %}
// use {{ options.base_namespace }};
use {{ options.base_request_namespace }};

/**
 * Class {{ classname }}
 * {{ api.get('displayName', '') }}
 * 
 * DOC: {{ api.get('apiDocPath', '') }}
 * SDK: {{ api.get('apiSdkPath', '') }}
 *
 * @package {{ namespace }}
 */
trait {{ classname }} // extends {{ options.base_cls }}
{

    
    ###################################################################
    ###########################  辅助函数 #########################
    ###################################################################

    protected static function _fixAndLogResult($request, $timeStart, array $requestArgs, $response, $method = '', $class = '', $line_no = '')
    {
        false && func_get_args();
        return [];
    }

    protected static function _fixAndLogException($request, $timeStart, array $requestArgs, \Exception $ex, $method = '', $class = '', $line_no = '')
    {
        false && func_get_args();
        return [];
    }

    protected static function _methodArgs(array $methodArgs, $methodName)
    {
        false && func_get_args();
        return [];
    }


    abstract public function getApiClient();

    ###################################################################
    ###########################  API 函数 #########################
    ###################################################################

    
    {%- for fname, finfo in api.get('api', []).items() %}

    {%- set params = options.api_args(fname, finfo.get('params', {})) %}
    /**
     * {{ api.get('cn', '') }}
     * {{ options.help_url(tag, fname) }}
     *
    {%- for agrs in params %}
     * @param {{ agrs['_type'] }} ${{ agrs['name'] }} {{ '必需' if agrs['required'] else '可选' }}  {{ agrs['cn'] }}
    {%- endfor %}
     * @return array
     */
    public function {{ fname[0].lower() + fname[1:] }}({{ options.build_api_args(fname, params) }})
    {
        $timeStart = microtime(true);

        $request = new {{ options.base_request }}('{{ _tag }}', '{{ ver }}', '{{ fname }}');
        $request->setMethod("POST");
        
        {%- for agrs in params %}
        {%- if fname.startswith('Describe') and agrs['name'] == 'startTime'  %}
        
        if (empty(${{ agrs['name'] }})) {
            ${{ agrs['name'] }} = Util::dateUTC({{ options.default_utc_date('Y-m-d 00:00:00', agrs['cn']) }});
        }
        $request->setQueryParameters('{{ agrs['key'] }}', ${{ agrs['name'] }});
        {%- elif fname.startswith('Describe') and agrs['name'] == 'endTime'  %}
        
        if (empty(${{ agrs['name'] }})) {
            ${{ agrs['name'] }} = Util::dateUTC({{ options.default_utc_date('Y-m-d H:i:s', agrs['cn']) }});
        }
        $request->setQueryParameters('{{ agrs['key'] }}', ${{ agrs['name'] }});
        {%- else %}
        
        {%- if agrs['required'] or agrs['name'] in ['pageNum', 'pageNumber'] %}
        $request->setQueryParameters('{{ agrs['key'] }}', ${{ agrs['name'] }});
        {%- else %}
        if (!empty(${{ agrs['name'] }})) {
            $request->setQueryParameters('{{ agrs['key'] }}', ${{ agrs['name'] }});
        }
        {%- endif %}
        
        {%- endif %}
        {%- endfor %}

        try {
            /** @var mixed $apiClient */
            $apiClient = $this->getApiClient();
            $response = $apiClient->getAcsResponse($request);
            return static::_fixAndLogResult($request, $timeStart, static::_methodArgs(func_get_args(), __METHOD__), $response, __METHOD__, __CLASS__, __LINE__);
        } catch (\Exception $ex) {
            return static::_fixAndLogException($request, $timeStart, static::_methodArgs(func_get_args(), __METHOD__), $ex, __METHOD__, __CLASS__, __LINE__);
        }
    }

    {% endfor %}
}