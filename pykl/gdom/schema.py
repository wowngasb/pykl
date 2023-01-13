# coding: utf-8
import graphene
import os
from gpage import Document, Element, Node, get_page
from gredis import RedisData, RedisInfo, RedisDbInfo, get_redis

class _HookProxy(object):
    def __init__(self, _get_page = None, _get_redis = None):
        self._get_page = _get_page
        self._get_redis = _get_redis

    def set_get_page(self, _get_page):
        self._get_page = _get_page

    def set_get_redis(self, _get_redis):
        self._get_redis = _get_redis

    def get_page(self, url):
        return self._get_page(url) if self._get_page else get_page(url)

    def get_redis(self, uri):
        return self._get_redis(uri) if self._get_redis else get_redis(uri)

HookProxy = _HookProxy()

class Query(graphene.ObjectType):
    page = graphene.Field(Document,
                          description='Visit the specified page',
                          url=graphene.String(description='The url of the page'),
                          _source=graphene.String(name='source', description='The source of the page')
                          )

    redis = graphene.Field(RedisData,
                          description='Visit the redis data',
                          uri=graphene.String(description='The uri of the redis')
                          )



    def resolve_page(self, args, context, info):
        url = args.get('url')
        source = args.get('source')
        assert url or source, 'At least you have to provide url or source of the page'
        if url.startswith('GitHub') and (url.endswith('.cache') or url.endswith('.html')):
            with open(os.path.join('D:\\', url), 'r') as rf:
                source = rf.read().decode('utf-8')
                url = ''

        return HookProxy.get_page(url or source)

    def resolve_redis(self, args, context, info):
        uri = args.get('uri')
        assert uri, 'At least you have to provide uri of the redis'
        return HookProxy.get_redis(uri)

schema = graphene.Schema(query=Query, types=[Element, RedisInfo, RedisDbInfo], auto_camelcase=False)

def main():
    import json
    from cmd import SAMPLE_REDIS_QUERY_MAP, SAMPLE_PAGE_QUERY_MAP
    test = SAMPLE_PAGE_QUERY_MAP['func_test']
    tmp = schema.execute(test)
    print 'data', json.dumps(tmp.data, indent=2)
    print 'errors', tmp.errors

if __name__ == '__main__':
    main()
