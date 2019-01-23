# -*- coding: utf-8 -*-
# code from py-googletrans
import ast
import json
import math
import random
import re
import time
from urllib.parse import urlencode

from aiohttp import ClientSession
from requests import Session

from linguister.const import DEFAULT_USER_AGENT
from linguister.exceptions import catch_req
from linguister.sdk import BaseTranslateSDK

BASE = 'https://translate.google.com'
TRANSLATE = 'https://{host}/translate_a/single'
LANGUAGES = {
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'en': 'english',
    'ja': 'japanese',
}
SPECIAL_CASES = {
    'ee': 'et',
}
LANGCODES = dict(map(reversed, LANGUAGES.items()))
EXCLUDES = ('en', 'ca', 'fr')

def legacy_format_json(original):
    # save state
    states = []
    text = original

    # save position for double-quoted texts
    for i, pos in enumerate(re.finditer('"', text)):
        # pos.start() is a double-quote
        p = pos.start() + 1
        if i % 2 == 0:
            nxt = text.find('"', p)
            states.append((p, text[p:nxt]))

    # replace all weired characters in text
    while text.find(',,') > -1:
        text = text.replace(',,', ',null,')
    while text.find('[,') > -1:
        text = text.replace('[,', '[null,')

    # recover state
    for i, pos in enumerate(re.finditer('"', text)):
        p = pos.start() + 1
        if i % 2 == 0:
            j = int(i / 2)
            nxt = text.find('"', p)
            # replacing a portion of a string use slicing to
            # extract those parts of the original string to be kept
            text = text[:p] + states[j][1] + text[nxt:]

    converted = json.loads(text)
    return converted


def format_json(original):
    try:
        converted = json.loads(original)
    except ValueError:
        converted = legacy_format_json(original)

    return converted

def rshift(val, n):
    """python port for '>>>'(right shift with padding)
    """
    return (val % 0x100000000) >> n

def build_params(query, src, dest, token):
    params = [
        ('client', 't'),
        ('sl', src),
        ('tl', dest),
        ('hl', dest),
        ('dt', 'at'),
        ('dt', 'bd'),
        ('dt', 'ex'),
        ('dt', 'ld'),
        ('dt', 'md'),
        ('dt', 'qca'),
        ('dt', 'rw'),
        ('dt', 'rm'),
        ('dt', 'ss'),
        ('dt', 't'),
        # 'dt': ['at', 'bd', 'ex', 'ld', 'md', 'qca', 'rw', 'rm', 'ss', 't'],
        ('ie', 'UTF-8'),
        ('oe', 'UTF-8'),
        ('otf', 1),
        ('ssel', 0),
        ('tsel', 0),
        ('tk', token),
        ('q', query),
    ]
    return params


class TokenAcquirer:
    """Google Translate API token generator

    translate.google.com uses a token to authorize the requests. If you are
    not Google, you do have this token and will have to pay for use.
    This class is the result of reverse engineering on the obfuscated and
    minified code used by Google to generate such token.

    The token is based on a seed which is updated once per hour and on the
    text that will be translated.
    Both are combined - by some strange math - in order to generate a final
    token (e.g. 744915.856682) which is used by the API to validate the
    request.

    This operation will cause an additional request to get an initial
    token from translate.google.com.

    Example usage:
        >>> from googletrans.gtoken import TokenAcquirer
        >>> acquirer = TokenAcquirer()
        >>> text = 'test'
        >>> tk = acquirer.do(text)
        >>> tk
        950629.577246
    """

    RE_TKK = re.compile(r'tkk:\'(.+?)\'', re.DOTALL)
    RE_RAWTKK = re.compile(r'tkk:\'(.+?)\'', re.DOTALL)

    def __init__(self, session, tkk='0', host='translate.google.com', proxy=None):
        self.session = session
        self.tkk = tkk
        self.host = host if 'http' in host else 'https://' + host
        self.proxy = proxy

    async def _update(self):
        """update tkk
        """
        # we don't need to update the base TKK value when it is still valid
        now = math.floor(int(time.time() * 1000) / 3600000.0)
        if self.tkk and int(self.tkk.split('.')[0]) == now:
            return

        r = await self.session.get(self.host, proxy=self.proxy)

        raw_tkk = self.RE_TKK.search(await r.text())
        if raw_tkk:
            self.tkk = raw_tkk.group(1)
            return

        # this will be the same as python code after stripping out a reserved word 'var'
        code = str(self.RE_TKK.search(r.text).group(1)).replace('var ', '')
        # unescape special ascii characters such like a \x3d(=)
        code = code.encode().decode('unicode-escape')
        if code:
            tree = ast.parse(code)
            visit_return = False
            operator = '+'
            n, keys = 0, dict(a=0, b=0)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    name = node.targets[0].id
                    if name in keys:
                        if isinstance(node.value, ast.Num):
                            keys[name] = node.value.n
                        # the value can sometimes be negative
                        elif isinstance(node.value, ast.UnaryOp) and \
                                isinstance(node.value.op, ast.USub):  # pragma: nocover
                            keys[name] = -node.value.operand.n
                elif isinstance(node, ast.Return):
                    # parameters should be set after this point
                    visit_return = True
                elif visit_return and isinstance(node, ast.Num):
                    n = node.n
                elif visit_return and n > 0:
                    # the default operator is '+' but implement some more for
                    # all possible scenarios
                    if isinstance(node, ast.Add):  # pragma: nocover
                        pass
                    elif isinstance(node, ast.Sub):  # pragma: nocover
                        operator = '-'
                    elif isinstance(node, ast.Mult):  # pragma: nocover
                        operator = '*'
                    elif isinstance(node, ast.Pow):  # pragma: nocover
                        operator = '**'
                    elif isinstance(node, ast.BitXor):  # pragma: nocover
                        operator = '^'
            # a safety way to avoid Exceptions
            clause = compile('{1}{0}{2}'.format(
                operator, keys['a'], keys['b']), '', 'eval')
            value = eval(clause, dict(__builtin__={}))
            result = '{}.{}'.format(n, value)

            self.tkk = result

    def _lazy(self, value):
        """like lazy evalution, this method returns a lambda function that
        returns value given.
        We won't be needing this because this seems to have been built for
        code obfuscation.

        the original code of this method is as follows:

           ... code-block: javascript

               var ek = function(a) {
                return function() {
                    return a;
                };
               }
        """
        return lambda: value

    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            d = rshift(a, d) if '+' == b[c + 1] else a << d
            a = a + d & 4294967295 if '+' == b[c] else a ^ d

            c += 3
        return a

    def acquire(self, text):
        a = []
        # Convert text to ints
        for i in text:
            val = ord(i)
            if val < 0x10000:
                a += [val]
            else:
                # Python doesn't natively use Unicode surrogates, so account for those
                a += [
                    math.floor((val - 0x10000)/0x400 + 0xD800),
                    math.floor((val - 0x10000)%0x400 + 0xDC00)
                    ]

        b = self.tkk if self.tkk != '0' else ''
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0

        # assume e means char code array
        e = []
        g = 0
        size = len(text)
        while g < size:
            l = a[g]
            # just append if l is less than 128(ascii: DEL)
            if l < 128:
                e.append(l)
            # append calculated value if l is less than 2048
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    # append calculated value if l matches special condition
                    if (l & 64512) == 55296 and g + 1 < size and \
                            a[g + 1] & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (a[g] & 1023) # This bracket is important
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
            g += 1
        a = b
        for i, value in enumerate(e):
            a += value
            a = self._xr(a, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0:  # pragma: nocover
            a = (a & 2147483647) + 2147483648
        a %= 1000000  # int(1E6)

        return '{}.{}'.format(a, a ^ b)

    async def do(self, text):
        await self._update()
        tk = self.acquire(text)
        return tk


class GoogleSDK(BaseTranslateSDK):

    def __init__(self, session, service_urls=None, proxy=None):
        super().__init__(session, proxy)
        self.service_urls = service_urls or ['translate.google.com']
        self.token_acquirer = TokenAcquirer(
            session=self.session, host=self.service_urls[0], proxy=self.proxy)

    def _pick_service_url(self):
        if len(self.service_urls) == 1:
            return self.service_urls[0]
        return random.choice(self.service_urls)

    async def _translate(self, text, dest, src):
        token = await self.token_acquirer.do(text)
        params = build_params(query=text, src=src, dest=dest, token=token)
        url = TRANSLATE.format(host=self._pick_service_url())
        r = await self._get(url, params=params)
        data = format_json(await r.text())
        return data

    def _parse_extra_data(self, data):
        response_parts_name_mapping = {
            0: 'translation',
            1: 'all-translations',
            2: 'original-language',
            5: 'possible-translations',
            6: 'confidence',
            7: 'possible-mistakes',
            8: 'language',
            11: 'synonyms',
            12: 'definitions',
            13: 'examples',
            14: 'see-also',
        }

        extra = {}

        for index, category in response_parts_name_mapping.items():
            extra[category] = data[index] if (index < len(data) and data[index]) else None

        return extra

    async def translate(self, text,  origin='auto', dest='zh-cn'):
        """Translate text from source language to destination language

        :param text: The source text(s) to be translated. Batch translation is supported via sequence input.
        :type text: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

        :param dest: The language to translate the source text into.
                     The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                     or one of the language names listed in :const:`googletrans.LANGCODES`.
        :param dest: :class:`str`; :class:`unicode`

        :param src: The language of the source text.
                    The value should be one of the language codes listed in :const:`googletrans.LANGUAGES`
                    or one of the language names listed in :const:`googletrans.LANGCODES`.
                    If a language is not specified,
                    the system will attempt to identify the source language automatically.
        :param src: :class:`str`; :class:`unicode`

        :rtype: Translated
        :rtype: :class:`list` (when a list is passed)

        Basic usage:
            >>> from googletrans import Translator
            >>> translator = Translator()
            >>> translator.translate('안녕하세요.')
            <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
            >>> translator.translate('안녕하세요.', dest='ja')
            <Translated src=ko dest=ja text=こんにちは。 pronunciation=Kon'nichiwa.>
            >>> translator.translate('veritas lux mea', src='la')
            <Translated src=la dest=en text=The truth is my light pronunciation=The truth is my light>

        Advanced usage:
            >>> translations = translator.translate(['The quick brown fox', 'jumps over', 'the lazy dog'], dest='ko')
            >>> for translation in translations:
            ...    print(translation.origin, ' -> ', translation.text)
            The quick brown fox  ->  빠른 갈색 여우
            jumps over  ->  이상 점프
            the lazy dog  ->  게으른 개
        """
        dest = dest.lower().split('_', 1)[0]
        origin = origin.lower().split('_', 1)[0]

        if origin != 'auto' and origin not in LANGUAGES:
            if origin in SPECIAL_CASES:
                origin = SPECIAL_CASES[origin]
            elif origin in LANGCODES:
                origin = LANGCODES[origin]
            else:
                raise ValueError('invalid source language')

        if dest not in LANGUAGES:
            if dest in SPECIAL_CASES:
                dest = SPECIAL_CASES[dest]
            elif dest in LANGCODES:
                dest = LANGCODES[dest]
            else:
                raise ValueError('invalid destination language')

        if isinstance(text, list):
            result = []
            for item in text:
                translated = self.translate(item, dest=dest, origin=origin)
                result.append(translated)
            return result

        origin = text
        data = await self._translate(text, dest, origin)

        # this code will be updated when the format is changed.
        translated = ''.join([d[0] if d[0] else '' for d in data[0]])

        extra_data = self._parse_extra_data(data)

        # actual source language that will be recognized by Google Translator
        # when the src passed is equal to auto.
        try:
            origin = data[2]
        except Exception:  # pragma: nocover
            pass

        pron = origin
        try:
            pron = data[0][1][-2]
        except Exception:  # pragma: nocover
            pass
        if dest in EXCLUDES and pron == origin:
            pron = translated

        result = {
            'src': origin,
            'dest': dest,
            'origin': origin,
            'text': translated,
            "pronunciation": pron,
            "extra_data": extra_data
        }

        return result

    def get_sentences(self, result):
        examples = []
        for i in result['extra_data']['examples'][0][:3]:
            examples.append({'example': i[0], 'translate': ''})
        return examples
    
    def get_means(self, result):
        means = []
        for mean in result['extra_data']['all-translations']:
            means.append(mean[0] + ' ' + '; '.join(mean[1]))
        return means
