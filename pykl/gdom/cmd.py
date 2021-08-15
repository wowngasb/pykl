import argparse
import json
import sys

import flask_graphql
from flask import Flask, Blueprint, url_for
from flask_graphql import GraphQLView

from schema import schema

SAMPLE_PAGE_QUERY_MAP = {
    'Hacker News Parser example': '''{
  page(url: "http://news.ycombinator.com") {
    items: query(selector: "tr.athing") {
      rank: text(selector: "td span.rank")
      title: text(selector: "td.title a")
      sitebit: text(selector: "span.comhead a")
      url: attr(selector: "td.title a", name: "href")
      attrs: next {
        score: text(selector: "span.score")
        user: text(selector: "a:eq(0)")
        comments: text(selector: "a:eq(2)")
      }
    }
  }
}''',
    'github pykl': '''{
  page(url: "https://github.com/wowngasb/pykl/") {
    items: query(selector: "div .Box-row", filter: "lambda el: len(el.children('div'))==4 ") {
      file: call(selector: "div", func: "lambda el: el[1].text()")
      ext: call(selector: "div", func: "lambda el: el[1].text().split('.')[-1] if el[1].text().find('.')>-1 else '' ")
      commit_text: call(selector: "div", func: "lambda el: el[2].text()")
      commit_id: call(selector: "div", func: "lambda el: el[2].find('a').attr('href').split('/')[-1] ")
      update_at: call(selector: "div", func: "lambda el: el[3].find('time-ago').attr('datetime') ")
    }
  }
}
''',


}

SAMPLE_REDIS_QUERY_MAP = {
    'test': '''{
  redis(uri: "redis://:auth@127.0.0.1") {
    test_info_info: info {
      redis_version
      db0: db_info(db: "db0") {
        keys
        expires
        avg_ttl
      }
    }
    test_key_ttl: ttl(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1")
    test_key_pttl: pttl(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1")
    test_key_type: type(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1")
    test_key_randomkey: randomkey
    test_string_get: get(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1")
    test_string_getrange: getrange(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1", start: 5, end: 20)
    test_string_getbit: getbit(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1", offset: 10)
    test_string_mget: mget(keys: ["BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1", "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1"])
    test_string_strlen: strlen(key: "BMCache:api\\\\AdminMgr._getReferralLink:admin_id=1")
    test_hash_hexists: hexists(key: "max_user", field: "chat_73")
    test_hash_hget: hget(key: "max_user", field: "chat_73")
    test_hash_hgetall: hgetall(key: "max_user") { key value }
    test_hash_hkeys: hkeys(key: "max_user")
    test_hash_hlen: hlen(key: "max_user")
    test_hash_hmget: hmget(key: "max_user", fields: ["chat_73", "chat_74"])
    test_hash_hvals: hvals(key: "max_user")
    test_list_lindex: lindex(key: "countly_action_raw", index: 2)
    test_list_llen: llen(key: "countly_action_raw")
    test_list_lrange: lrange(key: "countly_action_raw", start: 1, stop: 4)
    test_set_sdiff: sdiff(keys: ["mrq:known_queues", "mrq:known_queues"])
    test_set_sinter: sinter(keys: ["mrq:known_queues", "mrq:known_queues"])
    test_set_smembers: smembers(key: "mrq:known_queues")
    test_set_sunion: sunion(keys: ["mrq:known_queues", "mrq:known_queues"])
    test_set_srandmember: srandmember(key: "mrq:known_queues")
    test_set_srandmember2: srandmember(key: "mrq:known_queues", count: 2)
    test_zset_zcard: zcard(key: "salary")
    test_zset_zcount: zcount(key: "salary", min: "1000", max: "5000")
    test_zset_zlexcount: zlexcount(key: "myzset", min: "[b", max: "[f")
    test_zset_zrange: zrange(key: "salary", start: 1, stop: 3)
    test_zset_zrange_withscores: zrange_withscores(key: "salary", start: 1, stop: 3) { key value }
    test_zset_zrangebylex: zrangebylex(key: "myzset", min: "[b", max: "[f")
    test_zset_zrangebyscore: zrangebyscore(key: "salary", min: "1000", max: "5000")
    test_zset_zrangebyscore_withscores: zrangebyscore_withscores(key: "salary", min: "1000", max: "5000") { key value }
    test_zset_zrank: zrank(key: "salary", member: "joe")
    test_zset_zrevrange: zrevrange(key: "salary", start: 1, stop: 3)
    test_zset_zrevrange_withscores: zrevrange_withscores(key: "salary", start: 1, stop: 3) { key value }
    test_zset_zrevrangebyscore: zrevrangebyscore(key: "salary", min: "1000", max: "5000")
    test_zset_zrevrangebyscore_withscores: zrevrangebyscore_withscores(key: "salary", min: "1000", max: "5000") { key value }
    test_zset_zrevrank: zrevrank(key: "salary", member: "joe")
    test_zset_zscore: zscore(key: "salary", member: "joe")
    test_hyperloglog_pfcount:pfcount(keys: ["runoobkey"])
    test_hyperloglog_pfcount2:pfcount(keys: ["runoobkey", "runoobkey2"])
  }
}'''
}


def index_view():
    _str_p_a = lambda n, q: '<p><a href="{url}">{text}</a></p>'.format(text=n, url=url_for('graphql', query=q.strip()))
    _list_p_a = lambda d: [_str_p_a(n, q) for n, q in d.items()]
    return ''.join(
        ['<h2>Page:</h2>'] + _list_p_a(SAMPLE_PAGE_QUERY_MAP) +
        ['<h2>Redis:</h2>'] + _list_p_a(SAMPLE_REDIS_QUERY_MAP)
    )

def get_test_app():
    app = Flask(__name__)
    app.debug = True

    app.add_url_rule('/graphql', 'graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
    app.add_url_rule('/', 'index', view_func=index_view,)
    return app


def parse(query, source, page):
    execution = schema.execute(query, args={'page': page, 'source': source})
    if execution.errors:
        raise Exception(execution.errors[0])
    return execution.data


def main():
    parser = argparse.ArgumentParser(description='Parse and scrape any web page using GraphQL queries')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('query', type=argparse.FileType('r'), nargs='?', help='The query file', default=None)
    group.add_argument('--test', action='store_true', default=False, help='This will start a test server with a UI for querying')

    parser.add_argument('page', metavar='PAGE', nargs='?', const=1, type=str, help='The pages to parse')

    parser.add_argument('--source', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('--output', type=argparse.FileType('w'), default=sys.stdout)

    args = parser.parse_args()

    if args.test:
        app = get_test_app()
        import webbrowser
        webbrowser.open('http://localhost:5000/')

        app.run()
    else:
        query = args.query.read()
        page = args.page
        if not sys.stdin.isatty():
            source = args.source.read()
        else:
            source = None
        data = parse(query, source, page)
        outdata = json.dumps(data, indent=4, separators=(',', ': '))
        args.output.write(outdata)
        args.output.write('\n')

if __name__ == '__main__':
    main()
