#-*- coding: utf-8 -*-
import time
import binascii
import hashlib
import base64
import random

def __php_md5(*str_args):
    strin = ''.join(str_args)
    m2 = hashlib.md5()
    m2.update(strin)
    return m2.hexdigest()

def __php_base64_encode(strin):
    return base64.encodestring(strin).strip()

def __php_base64_decode(strin):
    try:
        return base64.decodestring(strin)
    except Exception:
        return ''

def _php_bin2hex(byte):
    return binascii.b2a_hex(byte)

def __php_hex2bin(strin):
    return binascii.a2b_hex(strin)

#########################################
##############  编码函数  ###############
#########################################


def int32ToByteWithLittleEndian(int32):
    int32 = abs(int(int32))
    byte0 = int32 % 256
    int32 = (int32 - byte0) / 256
    byte1 = int32 % 256
    int32 = (int32 - byte1) / 256
    byte2 = int32 % 256
    int32 = (int32 - byte2) / 256
    byte3 = int32 % 256
    return chr(byte0) + chr(byte1) + chr(byte2) + chr(byte3)


def byteToInt32WithLittleEndian(byte):
    byte_len = len(byte)
    byte0 = ord(byte[0]) if byte_len >=1 else 0
    byte1 = ord(byte[1]) if byte_len >=2 else 0
    byte2 = ord(byte[2]) if byte_len >=3 else 0
    byte3 = ord(byte[3]) if byte_len >=4 else 0
    return byte3 * 256 * 256 * 256 + byte2 * 256 * 256 + byte1 * 256 + byte0

def safe_base64_encode(str_):
    return __php_base64_encode(str_).replace('+', '-').replace('/', '_').rstrip('=')


def safe_base64_decode(str_):
    str_ = str_.strip().replace('-', '+').replace('_', '/')
    last_len = len(str_) % 4
    str_ = (str_ + '==') if last_len == 2 else (str_ + '=' if last_len == 3 else str_)
    return __php_base64_decode(str_)


def rand_str(length, tpl = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"):
    return ''.join([random.choice(tpl) for _ in range(length)]) if length > 0 else ''


def encode(string, key, expiry = 0, salt = 'salt', rnd_length = 2, chk_length = 4):
    ''' 加密函数
    `param str string` 需要加密的字符串
    `param str key`
    `param int expiry` 加密生成的数据 的 有效期 为0表示永久有效， 单位 秒
    `param str salt`
    `return str` 加密结果 使用了 safe_base64_encode
    '''
    return authcode(str(string), 'ENCODE', key, expiry, salt, rnd_length, chk_length)

def decode(string, key, salt = 'salt', rnd_length = 2, chk_length = 4):
    ''' 解密函数  成功返回原字符串  失败或过期 返回 空字符串
    `param str string` 需解密的 字符串 safe_base64_encode 格式编码
    `param str key`
    `param str salt`
    `return str` 解密结果
    '''
    return authcode(str(string), 'DECODE', key, 0, salt, rnd_length, chk_length)



def authcode(_string, operation, _key, _expiry, salt, rnd_length, chk_length):
    ''' 加解密函数
    `param str string`
    `param str operation`
    `param str key`
    `param int expiry`
    `param str salt`
    `param int rnd_length` 动态密匙长度，相同的明文会生成不同密文就是依靠动态密匙
    `param int chk_length`  校验和长度 byte $rnd_length>=4 && $rnd_length><=16
    `return str
    '''
    rnd_length = int(rnd_length) if rnd_length > 0 else 0
    _expiry = int(_expiry) if _expiry > 0 else 0
    chk_length = 4 if chk_length <= 4 else (int(chk_length) if chk_length < 16 else 16)

    time_int = int(time.time())
    key = __php_md5(salt, _key, 'origin key')# 密匙
    keya = __php_md5(salt, key[:16], 'key a for crypt')# 密匙a会参与加解密
    keyb = __php_md5(salt, key[16:32], 'key b for check sum')# 密匙b会用来做数据完整性验证

    if (operation == 'DECODE'):
        keyc = '' if rnd_length <= 0 else _string[:rnd_length]  # 密匙c用于变化生成的密文
        cryptkey = keya + __php_md5(salt, keya, keyc, 'merge key a and key c')# 参与运算的密匙
        # 解码，会从第 rnd_length Byte开始，因为密文前 rnd_length Byte保存 动态密匙
        string = safe_base64_decode(_string[rnd_length:])
        result = encodeByXor(string, cryptkey)
        # 验证数据有效性
        result_len_ = len(result)
        expiry_at_ = byteToInt32WithLittleEndian(result[:4]) if result_len_ >= 4 else 0
        pre_len = 4 + chk_length
        checksum_ = _php_bin2hex(result[4:pre_len]) if result_len_ >= pre_len else 0
        string_ = result[pre_len:] if result_len_ >= pre_len else ''
        tmp_sum = __php_md5(salt, string_, keyb)[: 2 * chk_length]
        test_pass = (expiry_at_ == 0 or expiry_at_ > time_int) and checksum_ == tmp_sum
        return string_ if test_pass else ''
    else:
        keyc = '' if rnd_length <= 0 else rand_str(rnd_length) # 密匙c用于变化生成的密文
        checksum = __php_md5(salt, _string, keyb)[: 2 * chk_length]
        expiry_at = _expiry + time_int if _expiry > 0 else 0
        cryptkey = keya + __php_md5(salt, keya, keyc, 'merge key a and key c')# 参与运算的密匙
        # 加密，原数据补充附加信息，共 8byte  前 4 Byte 用来保存时间戳，后 4 Byte 用来保存 checksum 解密时验证数据完整性
        # 解码，会从第 rnd_length Byte开始，因为密文前 rnd_length Byte保存 动态密匙
        string = ''.join([int32ToByteWithLittleEndian(expiry_at), __php_hex2bin(checksum), _string])
        result = encodeByXor(string, cryptkey)
        return keyc + safe_base64_encode(result)



def encodeByXor(string, cryptkey):
    string_length = len(string)
    key_length = len(cryptkey)
    result_list = []
    box = range(0, 256)
    rndkey = range(0, 256)
    # 产生密匙簿
    for i in range(0, 256):
        rndkey[i] = ord(cryptkey[i % key_length])

    j = 0
    for i in range(0, 256):
        j = (i + j + box[i] + box[j] + rndkey[i] + rndkey[j]) % 256
        tmp = box[i]
        box[i] = box[j]
        box[j] = tmp


    # 核心加解密部分
    a, j = 0, 0
    for i in range(0, string_length):
        a = (a + 1) % 256
        j = (j + box[a]) % 256
        tmp = box[a]
        box[a] = box[j]
        box[j] = tmp
        # 从密匙簿得出密匙进行异或，再转成字符
        tmp_idx = (box[a] + box[j]) % 256
        tmp_char = chr(ord(string[i]) ^ box[tmp_idx])
        result_list.append(tmp_char)

    result = ''.join(result_list)
    return result

def main():
    import json
    test = json.loads('''
{"key":"zT5hF$E24*(#dfS^Yq3&6A^6","test_list":{"CDveD0kGQkX6c":"","m1lFv6XGYEAe9z":"1","lJT_J__LJePfudOg":"12","dzWJrtwrqORxqOUJ4":"123","7r8Kqp3Fs3k5Dk3ZSp":"1234","q58an2EvsFuIuSevy2":"1234","qQDKgHWSuJFg-OCx-g":"1234","coJbrAR2BcNFy8IWkA":"1234","ewVITfifalugspmnN6":"1234"}}

''')
    key = '18fss45gre65q2%$@65e3276482'
    str_i = '123456'
    str_o = encode(str_i, key)
    str_i_ = decode(str_o, key)
    assert str_i==str_i_, 'error'
    _key = test['key']
    for v, t in test['test_list'].items():
        t_ = decode(v, _key)
        assert t==t_, 'error for %s %s but %s' % (t, v, t_)
        print 'pass decode("%s", "%s")="%s"' % (v, _key, t_)
    pass

if __name__ == '__main__':
    main()

