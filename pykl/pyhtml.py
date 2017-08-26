# -*- coding: utf-8 -*-


__all__ = ['tokenize', 'parse', 'prettify']

def tokenize(str_in):
    str_list = _html_list(str_in)
    return str_list

def _html_list(str_in, index=0, symbol=('<', '>', ' ', '/', '=', '!', )):
    """Returns a list from html parser consumes."""
    T1, T2, SP, SC, KV, SD = symbol
    ret_list = []
    lf = str_in.find(T1 , index)
    while lf >= index:
        nf = str_in.find(T2, lf)
        if lf>nf:
            break
        ret_obj, index = _get_mark(str_in, lf, nf, symbol)
        lf = str_in.find(T1, index)
        if ret_obj:
            ret_list.append(ret_obj)
    return ret_list

def _get_mark(str_in, ia, ib, symbol):
    T1, T2, SP, SC, KV, SD = symbol
    ret_obj = {"_ia":ia,"_ib":ib}  ## str_in[ia:ib+1]=<...>
    i_tag, i_sc = _skip(str_in, ia+1), str_in.rfind(SC, ia, ib)
    if ia<i_sc<ib and str_in[i_tag]==SC:
        ret_obj["_isc"] = 2   ## 2:like </div>
        ret_obj["_tag"] = str_in[i_sc+1:ib].strip()
    elif str_in[i_tag]==SD:
        ret_obj["_isc"] = 4   ## 2:like <!...>
        ret_obj["_tag"] = str_in[i_tag+1:ib].strip()
    else:
        ret_obj["_isc"] = 3 if ia<i_sc<ib and _skip(str_in, i_sc+1)==ib else 1
        ## 3:like <img .../>, 1:other <...>
        i_attr_end = i_sc if ret_obj["_isc"] == 3 else ib
        i_attr_start = str_in.find(SP, i_tag)
        if i_tag<i_attr_start<i_attr_end:
            ret_obj["_tag"] = str_in[i_tag:i_attr_start].strip()
            str_attr = str_in[i_attr_start+1:i_attr_end].strip()
            if str_attr:
                ret_obj["_attr"] = str_attr
                ret_obj["attr"] = _get_attr(str_attr, SP, KV)
        else:
            ret_obj["_tag"] = str_in[i_tag:i_attr_end].strip()

    return (ret_obj, ib+1)

def _get_attr(str_in, SP, KV, index=0):
    ret_obj = {}
    ll = len(str_in)
    while index < ll-1:
        ks_list, vs, index = _get_kv(str_in, index, ll, SP, KV)
        for ks in ks_list:
            ret_obj[ks] = vs
    return ret_obj

def _get_kv(str_in, index, ll, SP, KV):
    ks_list = []
    ks, index = _get_block(str_in, index, ll, SP, KV)
    if ks:
        ks_list.append(ks)
    vs, index = _get_block(str_in, index+1, ll, SP, KV) if str_in[index] == KV else (ks, index)
    while index<ll and str_in[index] == KV:
        if vs:
            ks_list.append(vs)
        vs, index = _get_block(str_in, index+1, ll, SP, KV)
    return (ks_list, vs, index)

def _get_block(str_in, index, ll, SP, KV, T="\\", STR={'"':1, "'":1, }):
    index = _skip(str_in, index)
    while str_in[index] == KV and index<ll-1:
        index = _skip(str_in, index+1)
    if index>=ll:
        return (None, ll)
    oi, tc, si, ki = index, str_in[index], str_in.find(SP, index), str_in.find(KV, index)
    if tc in STR:
        while not str_in[index+1] == tc:
            index += 2 if  str_in[index] == T else 1
        ret_str, index = str_in[oi+1:index+1], index+2
    elif index<si and (si<ki or ki<0):
        ret_str, index = str_in[oi:si], si
    elif index<ki and ( si>ki or si<0):
        ret_str, index = str_in[oi:ki], ki
    else:
        ret_str, index = str_in[index:], ll
    return (ret_str, index)

def _skip(str_in, index, B={' ':1, '\r':1, '\n':1, '\t':1, }):
    while str_in[index] in B:
        index += 1
    return index


def parse(html_obj):
    ret_print = {"_ia":1,"_ib":1, "_isc":1, "_tag":1, "_attr":0, "attr":1}
    _print_obj = [{k:v for k,v in i.items() if ret_print.get(k,0)} for i in html_obj]

    _inlen = len(_print_obj)
    print_obj = _fix_list(_print_obj, _inlen)

    inlen = len(print_obj)
    dom, outlen = _tree(print_obj, inlen, 0)

    if not outlen==inlen:
        raise EOFError('error end at %r!' % (print_obj[index:],))
    return dom

def _fix_list(html_list, list_len, index = 0):
    getit = lambda i:(html_list[i], html_list[i]["_isc"], html_list[i]["_tag"],)
    ret_list, tags = [], []
    while index<list_len:
        item, isc, tag = getit(index)
        if isc==1:
            ret_list.append(item)
            tags.append(tag)
        elif isc==2:
            if tags and tags[-1]==tag:
                ret_list.append(item)
                tags.pop()
            elif tags:
                ret_list.append({"_ia":0,"_ib":0, "_isc":2, "_tag":tags[-1],})
                tags.pop()
                continue
            else:
                ret_list.append({"_ia":0,"_ib":0, "_isc":1, "_tag":tag,})
                ret_list.append(item)
        else:
            ret_list.append(item)
        index += 1
    return ret_list

def _tree(html_list, list_len, index=0, nfind=None):
    dom = []
    _getit = lambda i:(html_list[i], html_list[i]["_isc"], html_list[i]["_tag"],)
    while index < list_len:
        item, isc, tag = _getit(index)
        if isc == 1:
            tmp, index = _tree(html_list, list_len, index+1, nfind=tag)
            if tmp:
                item['_sub'] = tmp
            _item, _isc, _tag = _getit(index)
            if not _tag==tag:
                raise EOFError('list not match at %r:%r!' % (item, _item))
            item['_ic'], item['_id'] = _item['_ia'], _item['_ib']
            dom.append(item)
        elif isc == 2:
            if nfind==tag:
                break
        elif isc == 3 or isc == 4:
            dom.append(item)
        index += 1
    return dom, index

def prettify(html_str, dom, sindex=0, indent=2, deep=0):
    indent = ' ' * indent if isinstance(indent, (int, long)) else indent
    ret_str = ''
    fixed = indent * deep
    _getit = lambda ele:(ele["_isc"], ele["_tag"], ele["_ia"], ele["_id"] if ele['_isc']==1 else ele["_ib"], ele.get('attr', {}))
    _join = lambda *ll: fixed + ''.join(ll) + '\n'
    _attr = lambda attr: ' ' + ' '.join(['%s=%r' % (k, str(v).decode("string_escape")) for k, v in attr.items()]) + ' ' if attr else ''
    for ele in dom:
        isc, tag, sidx, eidx, attr = _getit(ele)

        pre_text = html_str[sindex:sidx].strip()
        if pre_text:
            ret_str += _join(pre_text)

        if isc == 4:
            ret_str += _join('<!', tag, '>')
        elif isc == 3:
            ret_str += _join('<', tag, _attr(attr), '/>')
        elif isc == 1:
            ret_str += _join('<', tag, _attr(attr), '>')
            sub_dom = ele.get('_sub', [])
            if sub_dom:
                _sub_str, _sindex = prettify(html_str, sub_dom, sindex=ele['_ib'] + 1, indent=indent, deep=deep+1)
                ret_str += _sub_str
            else:
                _sindex = ele['_ib'] + 1

            iner_text = html_str[_sindex:ele['_ic']].strip()
            if iner_text:
                ret_str += indent + _join(iner_text)

            ret_str += _join('</', tag, '>')
        sindex = eidx + 1

    return ret_str, sindex

def main(str_in):
    html_str = str_in
    html_obj = tokenize(html_str)
    dom = parse(html_obj)

    import json
    msg = json.dumps(dom, ensure_ascii=False, indent=4)
    prettify_html, _ = prettify(html_str, dom, indent=4)

    with open('html.test.html', 'w') as ff:
        ff.write(prettify_html)

    with open('html.test.json', 'w') as ff:
        ff.write(msg)

if __name__=="__main__":
    print 'test start'
    str_t = u"""
TEST HTML
<!-- START #author-bio -->
<div class="entry">
    TEST TEXT
    <div class="copyright-area">
        本文由
        <a href="http://python.com">python</a>
        -
        <a href="http://www.python.com/pyper">PyPer</a>
        翻译
    </div>
    <div class="author-bio-info">
        <img src="http://www.python.com/pyper.jpg" />
        <span class="author-bio-info-block">
            主要关注 Python 脚本技术
            <br/>
        </span>
        <span class="author-bio-info-block">
            <a href="http://www.python.com/pyper" onclick="alert('xxx')" target="_blank">
            <i class="fa fa-user"></i>
            个人主页
            </a>
        </span>
    </div>
    <div class="clear"></div>
</div>
<!-- END #author-bio -->
"""
    main(str_t)
    print 'end'
