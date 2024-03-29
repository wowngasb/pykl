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


REPLACE_CACHE = {}


def _rep_find(s, fmt, last, seq):
    arr = [p for p in s.split(seq) if p]
    arr = arr[::-1] if last else arr
    for a in arr:
        if fmt == 'd' and a.isdigit():
            return a

    return ''


def build_replaces(replaces):
    if replaces in REPLACE_CACHE:
        return REPLACE_CACHE[replaces]

    arr = [r.split('|') for r in replaces.split(';') if '|' in r]
    arr = [a for a in arr if len(a) == 2]
    if not arr:
        return lambda s: s

    def rep2(s):
        if s is None:
            return s

        for aa in arr:
            p1, p2 = aa[0], aa[1]
            pchar, seq = (p1[0], p1[1:]) if p1 else ('', '')
            if pchar == '$' or pchar == '^':
                return _rep_find(s, p2, pchar == '$', seq if seq else '/')

            if p1 == '' and p2 == ' ':
                s = s.replace('\r', ' ')
                s = s.replace('\n', ' ')
                s = s.replace('\t', ' ')
                s = s.replace(u'\xa0', ' ')
                while '  ' in s:
                    s = s.replace('  ', ' ')
            elif p1 == '' and p2 == '':
                s = s.replace('\r', ' ')
                s = s.replace('\n', ' ')
                s = s.replace('\t', ' ')
                s = s.replace(u'\xa0', ' ')
                s = s.replace(' ', '')
            elif p1 == ':' and p2 == ':':
                s = s.replace(u'： ', p2)
                s = s.replace(u'：', p2)
            elif p1 == ',' and p2 == ',':
                s = s.replace(u'， ', p2)
                s = s.replace(u'，', p2)
            elif p1 == '.' and p2 == '.':
                s = s.replace(u'。 ', p2)
                s = s.replace(u'。', p2)
            else:
                s = s.replace(p1, p2)
        return s

    REPLACE_CACHE[replaces] = rep2
    return rep2


FUNC_CACHE = {}
for _i in range(100):
    FUNC_CACHE[str(_i)] = lambda els, idx=_i: els[idx].text() if len(els) > idx else ''

FUNC_CACHE[''] = FUNC_CACHE['0']


def _resolve_call(obj, args, context, info):
    replaces = args.get('replaces', '')
    rf = build_replaces(replaces) if replaces else None

    fstr = args.get('func', '')
    if fstr in FUNC_CACHE:
        func = FUNC_CACHE[fstr]
    else:
        func = eval(fstr)
        FUNC_CACHE[fstr] = func

    selector = args.get('selector')
    c_key = '__call_' + selector
    if hasattr(obj, c_key):
        el = getattr(obj, c_key)
    else:
        el = [i for i in _query_selector(obj, args).items()]
        setattr(obj, c_key, el)

    text = func(el) if el else ''
    return rf(text) if rf else text


class Node(graphene.Interface):
    '''A Node represents a DOM Node'''
    content = graphene.String(description='The html representation of the subnodes for the selected DOM',
                              selector=graphene.String())
    html = graphene.String(description='The html representation of the selected DOM',
                           selector=graphene.String())
    text = graphene.String(description='The text for the selected DOM',
                           selector=graphene.String(), replaces=graphene.String())

    texts = graphene.List(graphene.String, description='The text for the selected DOM',
                          selector=graphene.String(), replaces=graphene.String())

    call = graphene.String(description='The lambda result for the selected DOM',
                           selector=graphene.String(), replaces=graphene.String(), func=graphene.String())

    i_call = graphene.Int(description='The lambda result for the selected DOM',
                          selector=graphene.String(), replaces=graphene.String(), func=graphene.String())

    f_call = graphene.Float(description='The lambda result for the selected DOM',
                            selector=graphene.String(), replaces=graphene.String(), func=graphene.String())

    tag = graphene.String(description='The tag for the selected DOM',
                          selector=graphene.String())
    attr = graphene.String(description='The DOM attr of the Node',
                           selector=graphene.String(),
                           key=graphene.String(required=True))
    _is = graphene.Boolean(description='Returns True if the DOM matches the selector',
                           name='is', selector=graphene.String(required=True))
    query = graphene.List(lambda: Element,
                          description='Find elements using selector traversing down from self',
                          selector=graphene.String(required=True),
                          filter=graphene.String())
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
        replaces = args.get('replaces', '')
        rf = build_replaces(replaces) if replaces else None
        text = _query_selector(self, args).eq(0).remove('script').text()
        return rf(text) if rf else text

    def resolve_texts(self, args, context, info):
        replaces = args.get('replaces', '')
        rf = build_replaces(replaces) if replaces else None
        els = [i for i in _query_selector(self, args).items()]
        return [rf(el.text()) for el in els] if rf else [el.text() for el in els]

    def resolve_call(self, args, context, info):
        return _resolve_call(self, args, context, info)

    def resolve_f_call(self, args, context, info):
        ret = _resolve_call(self, args, context, info)
        return float(ret) if ret else 0.0

    def resolve_i_call(self, args, context, info):
        ret = _resolve_call(self, args, context, info)
        return int(ret) if ret else 0

    def resolve_tag(self, args, context, info):
        el = _query_selector(self, args).eq(0)
        if el:
            return el[0].tag

    def resolve__is(self, args, context, info):
        return self.is_(args.get('selector'))

    def resolve_attr(self, args, context, info):
        attr = args.get('key')
        return _query_selector(self, args).attr(attr)

    def resolve_query(self, args, context, info):
        filter = eval(args.get('filter', '')) if args.get('filter', '') else None
        return [i for i in _query_selector(self, args).items() if filter(i)] \
            if filter else \
            _query_selector(self, args).items()

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


def get_page(page):
    return pq(page)


class Document(graphene.ObjectType):
    '''
    The Document Type represent any web page loaded and
    serves as an entry point into the page content
    '''

    class Meta:
        interfaces = (Node,)

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
        interfaces = (Node,)

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
