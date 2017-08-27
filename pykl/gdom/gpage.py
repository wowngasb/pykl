# coding: utf-8
import graphene
from pyquery import PyQuery as pq
from collections import OrderedDict
import random

def _query_selector(pq, args):
    selector = args.get('selector')
    if not selector:
        return pq
    return pq.find(selector)


class Node(graphene.Interface):
    '''A Node represents a DOM Node'''
    content = graphene.String(description='The html representation of the subnodes for the selected DOM',
                              selector=graphene.String())
    html = graphene.String(description='The html representation of the selected DOM',
                           selector=graphene.String())
    text = graphene.String(description='The text for the selected DOM',
                           selector=graphene.String())

    call = graphene.String(description='The lambda result for the selected DOM',
                           selector=graphene.String(), func=graphene.String())

    tag = graphene.String(description='The tag for the selected DOM',
                          selector=graphene.String())
    attr = graphene.String(description='The DOM attr of the Node',
                           selector=graphene.String(),
                           _name=graphene.String(name='name', required=True))
    _is = graphene.Boolean(description='Returns True if the DOM matches the selector',
                           name='is', selector=graphene.String(required=True))
    query = graphene.List(lambda: Element,
                          description='Find elements using selector traversing down from self',
                          selector=graphene.String(required=True))
    children = graphene.List(lambda: Element,
                             description='The list of children elements from self',
                             selector=graphene.String())
    parents = graphene.List(lambda: Element,
                            description='The list of parent elements from self',
                            selector=graphene.String())
    parent = graphene.Field(lambda: Element,
                            description='The parent element from self')
    siblings = graphene.List(lambda: Element,
                             description='The siblings elements from self',
                             selector=graphene.String())
    next = graphene.Field(lambda: Element,
                          description='The immediately following sibling from self',
                          selector=graphene.String())
    next_all = graphene.List(lambda: Element,
                             description='The list of following siblings from self',
                             selector=graphene.String())
    prev = graphene.Field(lambda: Element,
                          description='The immediately preceding sibling from self',
                          selector=graphene.String())
    prev_all = graphene.List(lambda: Element,
                             description='The list of preceding siblings from self',
                             selector=graphene.String())

    def resolve_content(self, args, context, info):
        return _query_selector(self, args).eq(0).html()

    def resolve_html(self, args, context, info):
        return _query_selector(self, args).outerHtml()

    def resolve_text(self, args, context, info):
        return _query_selector(self, args).eq(0).remove('script').text()

    def resolve_call(self, args, context, info):
        func = eval(args.get('func'))
        el = [i for i in _query_selector(self, args).items()]
        return func(el)

    def resolve_tag(self, args, context, info):
        el = _query_selector(self, args).eq(0)
        if el:
            return el[0].tag

    def resolve__is(self, args, context, info):
        return self.is_(args.get('selector'))

    def resolve_attr(self, args, context, info):
        attr = args.get('name')
        return _query_selector(self, args).attr(attr)

    def resolve_query(self, args, context, info):
        return _query_selector(self, args).items()

    def resolve_children(self, args, context, info):
        selector = args.get('selector')
        return self.children(selector).items()

    def resolve_parents(self, args, context, info):
        selector = args.get('selector')
        return self.parents(selector).items()

    def resolve_parent(self, args, context, info):
        parent = self.parents().eq(-1)
        if parent:
            return parent

    def resolve_siblings(self, args, context, info):
        selector = args.get('selector')
        return self.siblings(selector).items()

    def resolve_next(self, args, context, info):
        selector = args.get('selector')
        _next = self.nextAll(selector)
        if _next:
            return _next.eq(0)

    def resolve_next_all(self, args, context, info):
        selector = args.get('selector')
        return self.nextAll(selector).items()

    def resolve_prev(self, args, context, info):
        selector = args.get('selector')
        prev = self.prevAll(selector)
        if prev:
            return prev.eq(0)

    def resolve_prev_all(self, args, context, info):
        selector = args.get('selector')
        return self.prevAll(selector).items()


USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]

def get_page(page):
    ADD_HEADER = OrderedDict([
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        ('Accept-Encoding', 'gzip, deflate, sdch'),
        ('Accept-Language', 'zh-CN,zh;q=0.8'),
        ('Cache-Control', 'max-age=0'),
        ('Upgrade-Insecure-Requests', '1'),
        ('User-Agent', random.choice(USER_AGENTS)),
    ])
    return pq(page, headers=ADD_HEADER)


class Document(graphene.ObjectType):
    '''
    The Document Type represent any web page loaded and
    serves as an entry point into the page content
    '''
    class Meta:
        interfaces = (Node, )

    title = graphene.String(description='The title of the document')

    @classmethod
    def is_type_of(cls, root, context, info):
        return isinstance(root, pq) or super(Document, cls).is_type_of(root, context, info)

    def resolve_title(self, args, context, info):
        return self.find('title').eq(0).text()


class Element(graphene.ObjectType):
    '''
    A Element Type represents an object in a Document
    '''
    class Meta:
        interfaces = (Node, )

    visit = graphene.Field(Document,
                           description='Visit will visit the href of the link and return the corresponding document')

    @classmethod
    def is_type_of(cls, root, context, info):
        return isinstance(root, pq) or super(Element, cls).is_type_of(root, context, info)

    def resolve_visit(self, args, context, info):
        # If is a link we follow through href attr
        # return the resulting Document
        if self.is_('a'):
            href = self.attr('href')
            return get_page(href)
