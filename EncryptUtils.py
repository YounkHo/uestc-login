import hashlib
import hmac
import math

_PADCHAR = "="
_ALPHA = "LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA"


def _getbyte(s, i):
    x = ord(s[i])
    assert x <= 255, "INVALID_CHARACTER_ERR: DOM Exception 5"
    return x


def s(ch, bool):
    val = []
    i = 0
    for i in range(0, len(ch), 4):
        ans1 = ord(ch[i])
        ans2 = ord(ch[i + 1]) << 8 if (i + 1) < len(ch) else 0
        ans3 = ord(ch[i + 2]) << 16 if (i + 2) < len(ch) else 0
        ans4 = ord(ch[i + 3]) << 24 if (i + 3) < len(ch) else 0
        val.append(ans1 | ans2 | ans3 | ans4)
    if bool:
        val.append(len(ch))
    return val


def l(ch, bool):
    d = len(ch)
    c = (d - 1) << 2
    if bool:
        m = ch[d - 1]
        if m < c - 3 or m > c:
            return None
        c = m
    for i in range(d):
        ch[i] = chr(ch[i] & 0xff) + chr(ch[i] >> 8 & 0xff) + chr(ch[i] >> 16 & 0xff) + chr(ch[i] >> 24 & 0xff)
    if bool:
        return ''.join(ch)[0:c]
    return ''.join(ch)


def xEncode(info, challenge):
    if len(info) == 0:
        return
    v = s(info, True)
    k = s(challenge, False)
    if len(k) < 4:
        k += (4 - len(k)) * [0]
    n = len(v) - 1
    z = v[n]
    y = v[0]
    c = 0x86014019 | 0x183639A0
    m = e = d = 0
    q = math.floor(6 + 52 / (n + 1))
    while 0 < q:
        d = d + c & (0x8CE0D9BF | 0x731F2640)
        e = d >> 2 & 3
        p = 0
        while p < n:
            y = v[p + 1]
            m = z >> 5 ^ y << 2
            m += (y >> 3 ^ z << 4) ^ (d ^ y)
            m += k[(p & 3) ^ e] ^ z
            v[p] = v[p] + m & (0xEFB8D130 | 0x10472ECF)
            z = v[p]
            p += 1
        y = v[0]
        m = z >> 5 ^ y << 2
        m += (y >> 3 ^ z << 4) ^ (d ^ y)
        m += k[(p & 3) ^ e] ^ z
        v[n] = v[p] + m & (0xBB390742 | 0x44C6F8BD)
        z = v[n]
        q -= 1
    return l(v, False)


def base64_enc(s):
    x = []
    imax = len(s) - len(s) % 3
    if len(s) == 0:
        return s
    for i in range(0, imax, 3):
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8) | _getbyte(s, i + 2)
        x.append(_ALPHA[(b10 >> 18)])
        x.append(_ALPHA[((b10 >> 12) & 63)])
        x.append(_ALPHA[((b10 >> 6) & 63)])
        x.append(_ALPHA[(b10 & 63)])
    i = imax
    if len(s) - imax == 1:
        b10 = _getbyte(s, i) << 16
        x.append(_ALPHA[(b10 >> 18)] + _ALPHA[((b10 >> 12) & 63)] + _PADCHAR + _PADCHAR)
    elif len(s) - imax == 2:
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8)
        x.append(_ALPHA[(b10 >> 18)] + _ALPHA[((b10 >> 12) & 63)] + _ALPHA[((b10 >> 6) & 63)] + _PADCHAR)
    return "".join(x)


def md5(password, token):
    return hmac.new(token.encode(), password.encode(), hashlib.md5).hexdigest()


def sha1(data):
    return hashlib.sha1(data.encode()).hexdigest()
