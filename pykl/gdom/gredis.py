# coding: utf-8
import graphene
from redis import Redis

def _query_cmd(rd, args):
    cmd = args.get('cmd')
    if not cmd:
        return rd
    return rd.find(cmd)

def get_redis(uri):
    return Redis.from_url(uri)

class KeyValueAsString(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()

class KeyValueAsInt(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Int()

class KeyValueAsID(graphene.ObjectType):
    key = graphene.String()
    value = graphene.ID()

class KeyValueAsBoolean(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Boolean()

class KeyValueAsFloat(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Float()


kv_pairs = lambda tmp, cls: [cls(key=k, value=v) for k,v in dict(tmp).items()]

# ====================================
# ============  Redis 键(key) ==============
# ====================================

class RedisKeyQuery(graphene.Interface):
    '''
    Redis 键(key)
    11	PTTL key  以毫秒为单位返回 key 的剩余的过期时间。  !Int
    12	TTL key  以秒为单位，返回给定 key 的剩余生存时间(TTL, time to live)。   !Int
    13	RANDOMKEY  从当前数据库中随机返回一个 key。  String
    16	TYPE key   返回 key 所储存的值的类型。  String   none (key不存在)  string (字符串)  list (列表)  set (集合)  zset (有序集)  hash (哈希表)
    '''
    pttl = graphene.Float(key=graphene.String(), description='以毫秒为单位返回 key 的剩余的过期时间')
    def resolve_pttl(self, args, context, info):
        key = args.get('key')
        return self.pttl(key)

    ttl = graphene.Int(
        key=graphene.String(),
        description='以秒为单位，返回给定 key 的剩余生存时间(TTL, time to live)'
    )
    def resolve_ttl(self, args, context, info):
        key = args.get('key')
        return self.ttl(key)

    randomkey = graphene.String(
        description='从当前数据库中随机返回一个 key'
    )
    def resolve_randomkey(self, args, context, info):
        return self.randomkey()

    type = graphene.String(
        key=graphene.String(),
        description='返回 key 所储存的值的类型。 String  none (key不存在) string (字符串) list (列表) set (集合) zset (有序集) hash (哈希表)'
    )
    def resolve_type(self, args, context, info):
        key = args.get('key')
        return self.type(key)

class RedisKeyMutation(graphene.Interface):
    '''
    Redis 键(key)
    1	DEL key  该命令用于在 key 存在时删除 key。  !Int
    2	DUMP key  序列化给定 key ，并返回被序列化的值。  String
    3	EXISTS key  检查给定 key 是否存在。  !Int  0 1
    4	EXPIRE key seconds  为给定 key 设置过期时间。 !Int  0 1
    5	EXPIREAT key timestamp EXPIREAT 的作用和 EXPIRE 类似，都用于为 key 设置过期时间。 不同在于 EXPIREAT 命令接受的时间参数是 UNIX 时间戳(unix timestamp)。  !Int  0 1
    6	PEXPIRE key milliseconds 设置 key 的过期时间以毫秒计。  !Int  0 1
    7	PEXPIREAT key milliseconds-timestamp  设置 key 过期时间的时间戳(unix timestamp) 以毫秒计  !Int  0 1
    8	KEYS pattern  查找所有符合给定模式( pattern)的 key 。  !List(String)
    9	MOVE key db  将当前数据库的 key 移动到给定的数据库 db 当中。  !Int  0 1
    10	PERSIST key  移除 key 的过期时间，key 将持久保持。  !Int  0 1
    14	RENAME key newkey   修改 key 的名称  ok error
    15	RENAMENX key newkey   仅当 newkey 不存在时，将 key 改名为 newkey 。  !Int  0 1
    '''

# ====================================
# ==========  Redis 字符串(String) ============
# ====================================

class RedisStringQuery(graphene.Interface):
    '''
    Redis 字符串(String)
    2	GET key  获取指定 key 的值。  String
    3	GETRANGE key start end  返回 key 中字符串值的子字符  String
    5	GETBIT key offset  对 key 所储存的字符串值，获取指定偏移量上的位(bit)。  !Int  0 1
    6	MGET key1 [key2..]  获取所有(一个或多个)给定 key 的值。  List(String)
    11	STRLEN key  返回 key 所储存的字符串值的长度。   !Int
    '''
    get = graphene.String(
        key=graphene.String(),
        description='获取指定 key 的值'
    )
    def resolve_get(self, args, context, info):
        key = args.get('key')
        return self.get(key)

    getrange = graphene.String(
        key=graphene.String(),
        start=graphene.Int(),
        end=graphene.Int(),
        description='返回 key 中字符串值的子字符'
    )
    def resolve_getrange(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        end = args.get('end')
        return self.getrange(key, start, end)

    getbit = graphene.Int(
        key=graphene.String(),
        offset=graphene.Int(),
        description='对 key 所储存的字符串值，获取指定偏移量上的位(bit)'
    )
    def resolve_getbit(self, args, context, info):
        key = args.get('key')
        offset = args.get('offset')
        return self.getbit(key, offset)

    mget = graphene.List(
        graphene.String,
        keys=graphene.List(graphene.String),
        description='获取所有(一个或多个)给定 key 的值'
    )
    def resolve_mget(self, args, context, info):
        keys = args.get('keys')
        tmp = self.mget(*keys)
        return list(tmp) if tmp else []

    strlen = graphene.Int(
        key=graphene.String(),
        description='返回 key 所储存的字符串值的长度'
    )
    def resolve_strlen(self, args, context, info):
        key = args.get('key')
        return self.strlen(key)

class RedisStringMutation(graphene.Interface):
    '''
    Redis 字符串(String)
    1	SET key value  设置指定 key 的值  ok
    4	GETSET key value  将给定 key 的值设为 value ，并返回 key 的旧值(old value)。  String
    7	SETBIT key offset value  对 key 所储存的字符串值，设置或清除指定偏移量上的位(bit)。  !Int  0 1
    8	SETEX key seconds value  将值 value 关联到 key ，并将 key 的过期时间设为 seconds (以秒为单位)。  ok
    9	SETNX key value  只有在 key 不存在时设置 key 的值。  !Int  0 1
    10	SETRANGE key offset value  用 value 参数覆写给定 key 所储存的字符串值，从偏移量 offset 开始。 !Int
    12	MSET key value [key value ...]  同时设置一个或多个 key-value 对。  ok
    13	MSETNX key value [key value ...]  同时设置一个或多个 key-value 对，当且仅当所有给定 key 都不存在。  !Int  0 1
    14	PSETEX key milliseconds value  这个命令和 SETEX 命令相似，但它以毫秒为单位设置 key 的生存时间，而不是像 SETEX 命令那样，以秒为单位。  ok
    15	INCR key  将 key 中储存的数字值增一。   !Int
    16	INCRBY key increment  将 key 所储存的值加上给定的增量值（increment） 。     !Int
    17	INCRBYFLOAT key increment  将 key 所储存的值加上给定的浮点增量值（increment） 。     !Float
    18	DECR key  将 key 中储存的数字值减一。     !Int
    19	DECRBY key decrement  key 所储存的值减去给定的减量值（decrement） 。
    20	APPEND key value  如果 key 已经存在并且是一个字符串， APPEND 命令将 value 追加到 key 原来的值的末尾。  !Int
    '''

# ====================================
# ===========  Redis 哈希(Hash)  ============
# ====================================

class RedisHashQuery(graphene.Interface):
    '''
    Redis 哈希(Hash)
    2	HEXISTS key field  查看哈希表 key 中，指定的字段是否存在。  !Int  0 1
    3	HGET key field  获取存储在哈希表中指定字段的值。  String
    4	HGETALL key  获取在哈希表中指定 key 的所有字段和值  List(String)
    7	HKEYS key  获取所有哈希表中的字段  List(String)
    8	HLEN key  获取哈希表中字段的数量  !Int
    9	HMGET key field1 [field2]  获取所有给定字段的值  List(String)
    13	HVALS key  获取哈希表中所有值  List(String)
    '''
    hexists = graphene.Boolean(
        key=graphene.String(),
        field=graphene.String(),
        description='查看哈希表 key 中，指定的字段是否存在'
    )
    def resolve_hexists(self, args, context, info):
        key = args.get('key')
        field = args.get('field')
        return self.hexists(key, field)

    hget = graphene.String(
        key=graphene.String(),
        field=graphene.String(),
        description='获取存储在哈希表中指定字段的值'
    )
    def resolve_hget(self, args, context, info):
        key = args.get('key')
        field = args.get('field')
        return self.hget(key, field)

    hgetall = graphene.List(
        KeyValueAsString,
        key=graphene.String(),
        description='获取在哈希表中指定 key 的所有字段和值'
    )
    def resolve_hgetall(self, args, context, info):
        key = args.get('key')
        tmp = self.hgetall(key)
        return kv_pairs(tmp, KeyValueAsString)

    hkeys = graphene.List(
        graphene.String,
        key=graphene.String(),
        description='获取所有哈希表中的字段'
    )
    def resolve_hkeys(self, args, context, info):
        key = args.get('key')
        tmp = self.hkeys(key)
        return list(tmp) if tmp else []

    hlen = graphene.Int(
        key=graphene.String(),
        description='获取哈希表中字段的数量'
    )
    def resolve_hlen(self, args, context, info):
        key = args.get('key')
        return self.hlen(key)

    hmget = graphene.List(
        graphene.String,
        key=graphene.String(),
        fields=graphene.List(graphene.String),
        description='获取所有哈希表中的字段'
    )
    def resolve_hmget(self, args, context, info):
        key = args.get('key')
        fields = args.get('fields')
        tmp = self.hmget(key, fields)
        return list(tmp) if tmp else []

    hvals = graphene.List(
        graphene.String,
        key=graphene.String(),
        description='获取所有哈希表中的字段'
    )
    def resolve_hvals(self, args, context, info):
        key = args.get('key')
        tmp = self.hvals(key)
        return list(tmp) if tmp else []

class RedisHashMutation(graphene.Interface):
    '''
    Redis 哈希(Hash)
    1	HDEL key field2 [field2]  删除一个或多个哈希表字段   !Int
    5	HINCRBY key field increment  为哈希表 key 中的指定字段的整数值加上增量 increment 。  !Int
    6	HINCRBYFLOAT key field increment  为哈希表 key 中的指定字段的浮点数值加上增量 increment 。 !Float
    10	HMSET key field1 value1 [field2 value2 ]  同时将多个 field-value (域-值)对设置到哈希表 key 中。  ok
    11	HSET key field value  将哈希表 key 中的字段 field 的值设为 value 。  !Int  0 1
    12	HSETNX key field value  只有在字段 field 不存在时，设置哈希表字段的值。  !Int  0 1
    14	HSCAN key cursor [MATCH pattern] [COUNT count]  迭代哈希表中的键值对。  func
    '''

# ====================================
# ============  Redis 列表(List)  ============
# ====================================

class RedisListQuery(graphene.Interface):
    '''
    Redis 列表(List)
    4	LINDEX key index   通过索引获取列表中的元素  String
    6	LLEN key   获取列表长度    !Int
    10	LRANGE key start stop   获取列表指定范围内的元素  List(String)
    '''
    lindex = graphene.String(
        key=graphene.String(),
        index=graphene.Int(),
        description='通过索引获取列表中的元素'
    )
    def resolve_lindex(self, args, context, info):
        key = args.get('key')
        index = args.get('index')
        return self.lindex(key, index)

    llen = graphene.Int(
        key=graphene.String(),
        description='获取列表长度'
    )
    def resolve_llen(self, args, context, info):
        key = args.get('key')
        return self.llen(key)

    lrange = graphene.List(
        graphene.String,
        key=graphene.String(),
        start=graphene.Int(),
        stop=graphene.Int(),
        description='获取列表指定范围内的元素'
    )
    def resolve_lrange(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        stop = args.get('stop')
        tmp = self.lrange(key, start, stop)
        return list(tmp) if tmp else []

class RedisListMutation(graphene.Interface):
    '''
    Redis 列表(List)
    1	BLPOP key1 [key2 ] timeout   移出并获取列表的第一个元素， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止。  (String, String)
    2	BRPOP key1 [key2 ] timeout   移出并获取列表的最后一个元素， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止。 (String, String)
    3	BRPOPLPUSH source destination timeout   从列表中弹出一个值，将弹出的元素插入到另外一个列表中并返回它； 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止。  (String, String)
    5	LINSERT key BEFORE|AFTER pivot value   在列表的元素前或者后插入元素    !Int
    7	LPOP key   移出并获取列表的第一个元素  String
    8	LPUSH key value1 [value2]   将一个或多个值插入到列表头部  !Int
    9	LPUSHX key value   将一个值插入到已存在的列表头部  !Int
    11	LREM key count value   移除列表元素     !Int
    12	LSET key index value   通过索引设置列表元素的值  ok
    13	LTRIM key start stop   对一个列表进行修剪(trim)，就是说，让列表只保留指定区间内的元素，不在指定区间之内的元素都将被删除。  ok
    14	RPOP key   移除并获取列表最后一个元素  String
    15	RPOPLPUSH source destination   移除列表的最后一个元素，并将该元素添加到另一个列表并返回  String
    16	RPUSH key value1 [value2]   在列表中添加一个或多个值    !Int
    17	RPUSHX key value   为已存在的列表添加值    !Int
    '''

# ====================================
# ============  Redis 集合(Set)  ============
# ====================================

class RedisSetQuery(graphene.Interface):
    '''
    Redis 集合(Set)
    3	SDIFF key1 [key2]   返回给定所有集合的差集   List(String)
    5	SINTER key1 [key2]   返回给定所有集合的交集  List(String)
    8	SMEMBERS key   返回集合中的所有成员    List(String)
    13	SUNION key1 [key2]   返回所有给定集合的并集  List(String)
    11	SRANDMEMBER key [count]   返回集合中一个或多个随机数  List(String)
    '''
    sdiff = graphene.List(
        graphene.String,
        keys=graphene.List(graphene.String),
        description='返回给定所有集合的差集'
    )
    def resolve_sdiff(self, args, context, info):
        keys = args.get('keys')
        tmp = self.sdiff(*keys)
        return list(tmp) if tmp else []

    sinter = graphene.List(
        graphene.String,
        keys=graphene.List(graphene.String),
        description='返回给定所有集合的交集'
    )
    def resolve_sinter(self, args, context, info):
        keys = args.get('keys')
        tmp = self.sinter(*keys)
        return list(tmp) if tmp else []

    smembers = graphene.List(
        graphene.String,
        key=graphene.String(),
        description='返回集合中的所有成员'
    )
    def resolve_smembers(self, args, context, info):
        key = args.get('key')
        tmp = self.smembers(key)
        return list(tmp) if tmp else []

    sunion = graphene.List(
        graphene.String,
        keys=graphene.List(graphene.String),
        description='返回所有给定集合的并集'
    )
    def resolve_sunion(self, args, context, info):
        keys = args.get('keys')
        tmp = self.sunion(*keys)
        return list(tmp) if tmp else []

    srandmember = graphene.List(
        graphene.String,
        key=graphene.String(),
        count=graphene.Argument(graphene.Int, default_value=1),
        description='返回集合中一个或多个随机数'
    )
    def resolve_srandmember(self, args, context, info):
        key = args.get('key')
        count = args.get('count')
        tmp = self.srandmember(key, count)
        return list(tmp) if tmp else []

class RedisSetMutation(graphene.Interface):
    '''
    Redis 集合(Set)
    1	SADD key member1 [member2]   向集合添加一个或多个成员     !Int
    2	SCARD key   获取集合的成员数     !Int
    4	SDIFFSTORE destination key1 [key2]   返回给定所有集合的差集并存储在 destination 中     !Int
    6	SINTERSTORE destination key1 [key2]   返回给定所有集合的交集并存储在 destination 中    !Int
    7	SISMEMBER key member   判断 member 元素是否是集合 key 的成员    !Int  0 1
    9	SMOVE source destination member   将 member 元素从 source 集合移动到 destination 集合  !Int  0 1
    10	SPOP key   移除并返回集合中的一个随机元素   String
    12	SREM key member1 [member2]   移除集合中一个或多个成员  !Int
    14	SUNIONSTORE destination key1 [key2]   所有给定集合的并集存储在 destination 集合中    !Int
    15	SSCAN key cursor [MATCH pattern] [COUNT count]   迭代集合中的元素   List(String)
    '''

# ====================================
# ========= Redis 有序集合(sorted set) ==========
# ====================================

class RedisZSetQuery(graphene.Interface):
    '''
    Redis 有序集合(sorted set)
    2	ZCARD key   获取有序集合的成员数    !Int
    3	ZCOUNT key min max   计算在有序集合中指定区间分数的成员数    !Int
    6	ZLEXCOUNT key min max   在有序集合中计算指定字典区间内成员数量    !Int
    7	ZRANGE key start stop [WITHSCORES]   通过索引区间返回有序集合成指定区间内的成员   List(String)
    8	ZRANGEBYLEX key min max [LIMIT offset count]   通过字典区间返回有序集合的成员  List(String)
    9	ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT]   通过分数返回有序集合指定区间内的成员    List(String)
    10	ZRANK key member   返回有序集合中指定成员的索引    Int
    15	ZREVRANGE key start stop [WITHSCORES]   返回有序集中指定区间内的成员，通过索引，分数从高到底   List(String)
    16	ZREVRANGEBYSCORE key max min [WITHSCORES]   返回有序集中指定分数区间内的成员，分数从高到低排序   List(String)
    17	ZREVRANK key member   返回有序集合中指定成员的排名，有序集成员按分数值递减(从大到小)排序   Int
    18	ZSCORE key member   返回有序集中，成员的分数值   String
    '''
    zcard = graphene.Int(
        key=graphene.String(),
        description='获取有序集合的成员数'
    )
    def resolve_zcard(self, args, context, info):
        key = args.get('key')
        return self.zcard(key)

    zcount = graphene.Int(
        key=graphene.String(),
        min=graphene.String(),
        max=graphene.String(),
        description='计算在有序集合中指定区间分数的成员数'
    )
    def resolve_zcount(self, args, context, info):
        key = args.get('key')
        min = args.get('min')
        max = args.get('max')
        return self.zcount(key, min, max)

    zlexcount = graphene.Int(
        key=graphene.String(),
        min=graphene.String(),
        max=graphene.String(),
        description='在有序集合中计算指定字典区间内成员数量'
    )
    def resolve_zlexcount(self, args, context, info):
        key = args.get('key')
        min = args.get('min')
        max = args.get('max')
        return self.zlexcount(key, min, max)

    zrange = graphene.List(
        graphene.String,
        key=graphene.String(),
        start=graphene.Int(),
        stop=graphene.Int(),
        description='通过索引区间返回有序集合成指定区间内的成员'
    )
    def resolve_zrange(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        stop = args.get('stop')
        tmp = self.zrange(key, start, stop)
        return list(tmp) if tmp else []

    zrange_withscores = graphene.List(
        KeyValueAsFloat,
        key=graphene.String(),
        start=graphene.Int(),
        stop=graphene.Int(),
        description='通过索引区间返回有序集合成指定区间内的成员 带有分数值'
    )
    def resolve_zrange_withscores(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        stop = args.get('stop')
        tmp = self.zrange(key, start, stop, withscores=True)
        return kv_pairs(tmp, KeyValueAsFloat)

    zrangebylex = graphene.List(
        graphene.String,
        key=graphene.String(),
        min=graphene.String(),
        max=graphene.String(),
        offset=graphene.Argument(graphene.Int, default_value=None),
        count=graphene.Argument(graphene.Int, default_value=None),
        description='通过字典区间返回有序集合的成员'
    )
    def resolve_zrangebylex(self, args, context, info):
        key = args.get('key')
        min = args.get('min')
        max = args.get('max')
        offset = args.get('offset', None)
        count = args.get('count', None)
        tmp = self.zrangebylex(key, min, max, start=offset, num=count)
        return list(tmp) if tmp else []

    zrangebyscore = graphene.List(
        graphene.String,
        key=graphene.String(),
        min=graphene.String(),
        max=graphene.String(),
        offset=graphene.Argument(graphene.Int, default_value=None),
        count=graphene.Argument(graphene.Int, default_value=None),
        description='通过分数返回有序集合指定区间内的成员'
    )
    def resolve_zrangebyscore(self, args, context, info):
        key = args.get('key')
        min = args.get('min')
        max = args.get('max')
        offset = args.get('offset', None)
        count = args.get('count', None)
        tmp = self.zrangebyscore(key, min, max, start=offset, num=count)
        return list(tmp) if tmp else []

    zrangebyscore_withscores = graphene.List(
        KeyValueAsFloat,
        key=graphene.String(),
        min=graphene.String(),
        max=graphene.String(),
        offset=graphene.Argument(graphene.Int, default_value=None),
        count=graphene.Argument(graphene.Int, default_value=None),
        description='通过分数返回有序集合指定区间内的成员  带有分数值'
    )
    def resolve_zrangebyscore_withscores(self, args, context, info):
        key = args.get('key')
        min = args.get('min')
        max = args.get('max')
        offset = args.get('offset', None)
        count = args.get('count', None)
        tmp = self.zrangebyscore(key, min, max, start=offset, num=count, withscores=True)
        return kv_pairs(tmp, KeyValueAsFloat)

    zrank = graphene.Int(
        key=graphene.String(),
        member=graphene.String(),
        description='返回有序集合中指定成员的索引'
    )
    def resolve_zrank(self, args, context, info):
        key = args.get('key')
        member = args.get('member')
        return self.zrank(key, member)

    zrevrange = graphene.List(
        graphene.String,
        key=graphene.String(),
        start=graphene.Int(),
        stop=graphene.Int(),
        description='返回有序集中指定区间内的成员，通过索引，分数从高到底'
    )
    def resolve_zrevrange(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        stop = args.get('stop')
        tmp = self.zrevrange(key, start, stop)
        return list(tmp) if tmp else []


    zrevrange_withscores = graphene.List(
        KeyValueAsFloat,
        key=graphene.String(),
        start=graphene.Int(),
        stop=graphene.Int(),
        description='返回有序集中指定区间内的成员，通过索引，分数从高到底  带有分数值'
    )
    def resolve_zrevrange_withscores(self, args, context, info):
        key = args.get('key')
        start = args.get('start')
        stop = args.get('stop')
        tmp = self.zrevrange(key, start, stop, withscores=True)
        return kv_pairs(tmp, KeyValueAsFloat)

    zrevrangebyscore = graphene.List(
        graphene.String,
        key=graphene.String(),
        max=graphene.String(),
        min=graphene.String(),
        description='返回有序集中指定分数区间内的成员，分数从高到低排序'
    )
    def resolve_zrevrangebyscore(self, args, context, info):
        key = args.get('key')
        max = args.get('max')
        min = args.get('min')
        tmp = self.zrevrangebyscore(key, max, min)
        return list(tmp) if tmp else []

    zrevrangebyscore_withscores = graphene.List(
        KeyValueAsFloat,
        key=graphene.String(),
        max=graphene.String(),
        min=graphene.String(),
        description='返回有序集中指定分数区间内的成员，分数从高到低排序  带有分数值'
    )
    def resolve_zrevrangebyscore_withscores(self, args, context, info):
        key = args.get('key')
        max = args.get('max')
        min = args.get('min')
        tmp = self.zrevrangebyscore(key, max, min, withscores=True)
        return kv_pairs(tmp, KeyValueAsFloat)


    zrevrank = graphene.Int(
        key=graphene.String(),
        member=graphene.String(),
        description='返回有序集合中指定成员的排名，有序集成员按分数值递减(从大到小)排序'
    )
    def resolve_zrevrank(self, args, context, info):
        key = args.get('key')
        member = args.get('member')
        return self.zrevrank(key, member)

    zscore = graphene.String(
        key=graphene.String(),
        member=graphene.String(),
        description='返回有序集中，成员的分数值'
    )
    def resolve_zscore(self, args, context, info):
        key = args.get('key')
        member = args.get('member')
        return self.zscore(key, member)

class RedisZSetMutation(graphene.Interface):
    '''
    Redis 有序集合(sorted set)
    1	ZADD key score1 member1 [score2 member2]   向有序集合添加一个或多个成员，或者更新已存在成员的分数   !Int
    4	ZINCRBY key increment member   有序集合中对指定成员的分数加上增量 increment  String
    5	ZINTERSTORE destination numkeys key [key ...]   计算给定的一个或多个有序集的交集并将结果集存储在新的有序集合 key 中
    11	ZREM key member [member ...]   移除有序集合中的一个或多个成员   !Int
    12	ZREMRANGEBYLEX key min max   移除有序集合中给定的字典区间的所有成员    !Int
    13	ZREMRANGEBYRANK key start stop   移除有序集合中给定的排名区间的所有成员    !Int
    14	ZREMRANGEBYSCORE key min max   移除有序集合中给定的分数区间的所有成员   !Int
    19	ZUNIONSTORE destination numkeys key [key ...]   计算给定的一个或多个有序集的并集，并存储在新的 key 中    !Int
    20	ZSCAN key cursor [MATCH pattern] [COUNT count]   迭代有序集合中的元素（包括元素成员和元素分值）  func
    '''


# ====================================
# ========= Redis 有序集合(sorted set) ==========
# ====================================

class RedisHyperLogLogQuery(graphene.Interface):
    '''
    Redis HyperLogLog
    2	PFCOUNT key [key ...]   返回给定 HyperLogLog 的基数估算值。      !Int
    '''
    pfcount = graphene.Int(
        keys=graphene.List(graphene.String),
        description='返回给定 HyperLogLog 的基数估算值'
    )
    def resolve_pfcount(self, args, context, info):
        keys = args.get('keys')
        return self.pfcount(*keys)

class RedisHyperLogLogMutation(graphene.Interface):
    '''
    Redis HyperLogLog
    1	PFADD key element [element ...]   添加指定元素到 HyperLogLog 中。     !Int  0 1
    3	PFMERGE destkey sourcekey [sourcekey ...]   将多个 HyperLogLog 合并为一个 HyperLogLog    ok
    '''


# ====================================
# ============== Redis Info ==============
# ====================================

class RedisDbInfo(graphene.ObjectType):
    avg_ttl = graphene.Float()
    expires = graphene.Int()
    keys = graphene.Int()

class RedisInfo(graphene.ObjectType):
    aof_current_rewrite_time_sec = graphene.Int()
    aof_enabled = graphene.Int(description='redis是否开启了aof')
    aof_last_bgrewrite_status = graphene.String()
    aof_last_rewrite_time_sec = graphene.Int()
    aof_last_write_status = graphene.String()
    aof_rewrite_in_progress = graphene.Int()
    aof_rewrite_scheduled = graphene.Int()
    arch_bits = graphene.Int()
    blocked_clients = graphene.Int()
    client_biggest_input_buf = graphene.Int()
    client_longest_output_list = graphene.Int()
    config_file = graphene.String()
    connected_clients = graphene.Int(description='连接的客户端数量')
    connected_slaves = graphene.Int(description='slave的数量')
    evicted_keys = graphene.Int(description='运行以来删除过的key的数量')
    expired_keys = graphene.Int(description='运行以来过期的 key 的数量')
    gcc_version = graphene.String(description='gcc版本号')
    hz = graphene.Int()
    instantaneous_ops_per_sec = graphene.Int()
    keyspace_hits = graphene.Int(description='命中 key 的次数')
    keyspace_misses = graphene.Int(description='不命中 key 的次数')
    latest_fork_usec = graphene.Int()
    loading = graphene.Int()
    lru_clock = graphene.Int()
    master_repl_offset = graphene.Int()
    mem_allocator = graphene.String()
    mem_fragmentation_ratio = graphene.Float(description='内存碎片比率')
    multiplexing_api = graphene.String()
    os = graphene.String()
    process_id = graphene.Int(description='当前 Redis 服务器进程id')
    pubsub_channels = graphene.Int(description='当前使用中的频道数量')
    pubsub_patterns = graphene.Int(description='当前使用的模式的数量')
    rdb_bgsave_in_progress = graphene.Int(description='后台进行中的 save 操作的数量')
    rdb_changes_since_last_save = graphene.Int(description='上次保存数据库之后，执行命令的次数')
    rdb_current_bgsave_time_sec = graphene.Int()
    rdb_last_bgsave_status = graphene.String()
    rdb_last_bgsave_time_sec = graphene.Int()
    rdb_last_save_time = graphene.Int(description='最后一次成功保存的时间点，以 UNIX 时间戳格式显示')
    redis_build_id = graphene.String()
    redis_git_dirty = graphene.Int()
    redis_git_sha1 = graphene.Int()
    redis_mode = graphene.String()
    redis_version = graphene.String(description='redis 的版本')
    rejected_connections = graphene.Int()
    repl_backlog_active = graphene.Int()
    repl_backlog_first_byte_offset = graphene.Int()
    repl_backlog_histlen = graphene.Int()
    repl_backlog_size = graphene.Int()
    role = graphene.String(description='当前实例的角色master还是slave')
    run_id = graphene.String()
    sync_full = graphene.Int()
    sync_partial_err = graphene.Int()
    sync_partial_ok = graphene.Int()
    tcp_port = graphene.Int()
    total_commands_processed = graphene.Int(description='运行以来执行过的命令的总数量')
    total_connections_received = graphene.Int(description='运行以来连接过的客户端的总数量')
    uptime_in_days = graphene.Int(description='运行时间(天)')
    uptime_in_seconds = graphene.Int(description='运行时间(秒)')
    used_cpu_sys = graphene.Float()
    used_cpu_sys_children = graphene.Float()
    used_cpu_user = graphene.Float()
    used_cpu_user_children = graphene.Float()
    used_memory = graphene.Int(description='Redis 分配的内存总量')
    used_memory_human = graphene.String()
    used_memory_lua = graphene.Int()
    used_memory_peak = graphene.Int()
    used_memory_peak_human = graphene.String(description='Redis所用内存的高峰值')
    used_memory_rss = graphene.Int(description='Redis 分配的内存总量(包括内存碎片)')
    bgrewriteaof_in_progress = graphene.Int(description='后台进行中的 aof 文件修改操作的数量')

    db_info = graphene.Field(RedisDbInfo, args={
        'db': graphene.Argument(graphene.String, default_value='db0')
    }, description='具体的db详细信息')

    def resolve_db_info(self, args, context, info):
        tmp = args.get('db')
        return RedisDbInfo(**self._ext_data.get(tmp, {}))


# ====================================
# =========== Redis ObjectType ============
# ====================================

class RedisData(graphene.ObjectType):
    '''
    The Document Type represent any web page loaded and
    serves as an entry point into the page content
    '''
    class Meta:
        interfaces = (
            RedisKeyQuery,
            RedisStringQuery,
            RedisHashQuery,
            RedisListQuery,
            RedisSetQuery,
            RedisZSetQuery,
            RedisHyperLogLogQuery,
        )
        '''
            # 查询操作
            RedisKeyQuery,
            RedisStringQuery,
            RedisHashQuery,
            RedisListQuery,
            RedisSetQuery,
            RedisZSetQuery,
            RedisHyperLogLogQuery,
            # 修改操作
            RedisKeyMutation,
            RedisStringMutation,
            RedisHashMutation,
            RedisListMutation,
            RedisSetMutation,
            RedisZSetMutation,
            RedisHyperLogLogMutation
        '''

    info = graphene.Field(RedisInfo, description='The info of the redis')
    def resolve_info(self, args, context, info):
        info = self.info()
        data_dict = {key: info.pop(key, None) for key in RedisInfo._meta.fields}
        redis_info = RedisInfo(**data_dict)
        setattr(redis_info, '_ext_data', info)
        return redis_info
