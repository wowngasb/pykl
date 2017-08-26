# coding: utf-8
import graphene

from gpage import Document, Element, Node, get_page
from gredis import RedisData, RedisInfo, RedisDbInfo, get_redis

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
        return get_page(url or source)

    def resolve_redis(self, args, context, info):
        uri = args.get('uri')
        assert uri, 'At least you have to provide uri of the redis'
        return get_redis(uri)

schema = graphene.Schema(query=Query, types=[Element, RedisInfo, RedisDbInfo], auto_camelcase=False)

def main():
    import json
    from cmd import SAMPLE_REDIS_QUERY_MAP
    test = SAMPLE_REDIS_QUERY_MAP['test']
    tmp = schema.execute(test)
    print 'data', json.dumps(tmp.data, indent=2)
    print 'errors', tmp.errors

if __name__ == '__main__':
    main()
