#-*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
import urllib2
import httplib
import socket
import gzip
import datetime
import random
import StringIO

ALL_ERROR = Exception

HTTP_TIME_OUT = 30

class Error(Exception):
    pass

class HttpError(Error):
    pass

class HttpNetError(HttpError):
    pass

ADD_HEADER = (
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
    ('Accept-Encoding', 'gzip, deflate, sdch'),
    ('Accept-Language', 'zh-CN,zh;q=0.8'),
    ('Cache-Control', 'max-age=0'),
    ('Upgrade-Insecure-Requests', '1'),
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'),
)

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


def get_url(url, use_gzip=True, proxy_info=None, timeout=HTTP_TIME_OUT, add_header=ADD_HEADER, random_agent=True):
    url = url.strip()
    if not url:
        return ''

    try:
        return _get_url(url, use_gzip=use_gzip, proxy_info=proxy_info, timeout=timeout, add_header=add_header, random_agent=random_agent)
    except urllib2.HTTPError as ex:
        status_code = getattr(ex, 'code', 0)
        error_cls = type('HttpError%d' % (status_code, ), (HttpError, ), {}) if status_code > 0 else HttpError
        raise error_cls('get_data http error:%d %s <%s>' % (ex.code, ex, proxy_info))
    except urllib2.URLError as ex:
        if isinstance(getattr(ex, 'reason', None), socket.error):
            raise HttpNetError('get_data socket error:%d %s <%s>' % (ex.reason.errno if ex.reason.errno else 0, ex, proxy_info))
        else:
            raise HttpNetError('get_data urlerror error:%d %s <%s>' % (ex.code, ex, proxy_info))
    except socket.error as ex:
        raise HttpNetError('get_data socket error:%d %s <%s>' % (ex.errno if ex.errno else 0, ex, proxy_info))
    except httplib.BadStatusLine as ex:
        raise HttpNetError('get_data httplib BadStatusLine:%s <%s>' % (ex, proxy_info))
    except ALL_ERROR as ex:
        raise ex

def _get_url(url, use_gzip, proxy_info, timeout, add_header, random_agent):
    if proxy_info:
        p_type = 'https' if  isinstance(proxy_info, (tuple, list)) and len(proxy_info)>=3 and proxy_info[2] == 'https' else 'http'
        p_host = "%s:%d" % proxy_info[:2] if  isinstance(proxy_info, (tuple, list)) and len(proxy_info)>=2 else str(proxy_info)
        p_value = {p_type : p_type + "://" + p_host}
        proxy_support = urllib2.ProxyHandler(p_value)
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)

    req = urllib2.Request(url)
    for tag, val in add_header:
        if tag == 'Accept-Encoding':
            if not use_gzip:
                val = val.replace('gzip, ', '').replace('gzip,', '').replace('gzip', '')
        if tag == 'User-Agent':
            if random_agent:
                val = random.choice(USER_AGENTS)
        req.add_header(tag, val)

    res = urllib2.urlopen(req, timeout=timeout)

    headers, data = res.headers, res.read()
    if headers.getheader('Content-Encoding', default='').lower()=='gzip':
        try:
            data = gzip.GzipFile(fileobj=StringIO.StringIO(data)).read()
        except KeyboardInterrupt as ex:
            raise ex
        except ALL_ERROR:
            if use_gzip:
                return _get_url(url, use_gzip=False, timeout=timeout, proxy_info=proxy_info, random_agent=random_agent)

    return headers, data

class MultiHttpDownLoad(object):
    add_header = (
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        ('Accept-Encoding', 'gzip, deflate, sdch'),
        ('Accept-Language', 'zh-CN,zh;q=0.8'),
        ('Cache-Control', 'max-age=0'),
        ('Upgrade-Insecure-Requests', '1'),
        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'),
    )

    def __init__(self, spawn_num, error_max=5, http_time_out=HTTP_TIME_OUT, get_proxy=None, logger=None):
        self.spawn_num = int(spawn_num)
        self.error_max = int(error_max)
        self.http_time_out = int(http_time_out)
        self.get_proxy = get_proxy
        self.logger = logger

    def log(self, msg, tag='DEBUG'):
        tag = tag.upper()
        if self.logger and getattr(self.logger, 'log', None):
            logger.log(msg, tag)
        else:
            time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            print '%s [%s] %s' % (time_str, tag, msg)

    def get_http_list(self, url_list, do_data, isok_func=lambda d,h:isinstance(d, str) and d, use_gzip=True):
        def _do_get(idx, url, isok_func, use_gzip):
            data, headers = self._get_data(url, isok_func, use_gzip)
            self.log('get data:%s(length:%d)<idx:%d>' % (url, len(data), idx), 'INFO')
            do_data(url, data, headers)

        if not hasattr(do_data, '__call__') or not hasattr(isok_func, '__call__'):
            fault_msg = 'do_data and isok_func must be callable'
            self.log(fault_msg, 'FAULT')
            raise ValueError(fault_msg)
        if not url_list:
            return None

        gpool = Pool(self.spawn_num) if self.spawn_num > 1 else None
        for idx, url in enumerate(url_list):
            if self.spawn_num>1:
                gpool.spawn(_do_get, idx, url, isok_func, use_gzip)
            else:
                _do_get(idx, url, isok_func, use_gzip)

        if self.spawn_num>1:
            gpool.join()

    def _get_proxy(self):
        return self.get_proxy() if self.get_proxy else None

    def _get_data(self, url, isok_func, use_gzip):
        data, headers, proxy_info = '', {}, None
        error_count = 0
        while 1:
            if data is None:
                proxy_info = self._get_proxy()
                error_count += 1
                self.log('%suse proxy:%s(%s)<err:%d>' % ('.'*error_count, url, proxy_info, error_count), 'ERROR')
                if error_count >= self.error_max:
                    self.log('failure in:%s' % (url, ), 'FAULT')
                    return '', {}

            try:
                data, headers, proxy_info = self._get_url(url, use_gzip=use_gzip, proxy_info=proxy_info)
            except urllib2.HTTPError as ex:
                self.log('get_data http error:%d %s <%s>' % (ex.code, ex, proxy_info), 'ERROR')
            except urllib2.URLError as ex:
                if isinstance(getattr(ex, 'reason', None), socket.error):
                    self.log('get_data socket error:%d %s <%s>' % (ex.reason.errno if ex.reason.errno else 0, ex, proxy_info), 'ERROR')
                else:
                    self.log('get_data urlerror error:%d %s <%s>' % (ex.code, ex, proxy_info), 'ERROR')
            except socket.error as ex:
                self.log('get_data socket error:%d %s <%s>' % (ex.errno if ex.errno else 0, ex, proxy_info), 'ERROR')
            except httplib.BadStatusLine as ex:
                self.log('get_data httplib BadStatusLine:%s <%s>' % (ex, proxy_info), 'ERROR')
            except Exception as ex:
                self.log('get_data error:%s <%s>' % (ex, proxy_info), 'ERROR')

            if isok_func(data, headers):
                return data, headers
            else:
                data = None

    def _get_url(self, url, use_gzip=True, proxy_info=None):
        if not url:
            return '', {}, None
        headers, data = get_url(url, use_gzip=True, proxy_info=None, timeout=HTTP_TIME_OUT, add_header=ADD_HEADER, random_agent=True)
        return data, dict(headers), proxy_info


def main():

    test = MultiHttpDownLoad(50)

    url_file_map = {
        'http://baidu.com': 'baidu.html',
        'http://g.cn': 'google.html',
        #'http://facebook.com': 'facebook.html'
    }

    def do_data(url, data, headers):
        file_str = url_file_map.get(url, '')
        print file_str, url, 'len:', len(data)

    test.get_http_list(url_file_map.keys() * 5, do_data)

if __name__ == '__main__':
    main()

