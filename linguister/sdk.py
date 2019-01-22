from collections import OrderedDict
from functools import wraps
import hashlib
from importlib import import_module
import os
import random
import string
import time
from urllib.parse import urlencode
from uuid import uuid4

from linguister.exceptions import (catch_req, SymbolException, NotSupportLangException)


class BaseTranslateSDK:
    zh = 'zh' # China
    en = 'en' # English
    jp = 'jp' # Japan
    de = 'de' # German
    fr = 'fr' # France
    es = 'es' # Spain

    def generate_random_str(self, length=24) -> str:
        return ''.join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(24))

    def generate_timestamp(self) -> int:
        return int(time.time())

    def trans_symbol(self, origin, dest):
        if not (hasattr(self, origin) and hasattr(self, dest)):
            raise NotSupportLangException()

        return getattr(self, origin), getattr(self, dest)

class YouDaoSDK:
    """
    app_key: Application key
    app_id : Application ID
    """

    def __init__(self,
                 session,
                 suggest_url='http://dict.youdao.com/suggest',
                 paraphrase_url="http://dict.youdao.com/jsonapi",
                 translate_url="http://fanyi.youdao.com/translate"):
        self.session = session
        self.suggest_url = suggest_url
        self.paraphrase_url = paraphrase_url
        self.translate_url = translate_url

    async def interface(self, word, lang='eng', num=5, doctype='json'):
        return await self.session.get(
            self.suggest_url,
            params={
                'q': word,
                'le': lang,
                'num': num,
                'doctype': doctype
            })

    @catch_req()
    async def paraphrase(self,
                         word,
                         jsonversion=2,
                         client='mobile',
                         dict_list=[[
                             "ec",
                             "ce",
                             "simple",
                             "phrs",
                         ], "fanyi", "ugc"],
                         network='wifi'):
        dicts_len = len(dict_list)
        dicts_list_cache = []
        for i in dict_list:
            if isinstance(i, list):
                dicts_list_cache.append(i)
            else:
                dicts_list_cache.append([i])

        dicts = {"count": dicts_len, "dicts": dicts_list_cache}
        params = urlencode({
                'jsonversion': jsonversion,
                'client': client,
                'q': word,
                'dicts': dicts,
                'network': network
            })
        return await self.session.get(
            self.paraphrase_url + '?' + params)

    @staticmethod
    def get_mean_list(dict_):
        result = []
        if dict_.get('ec'):
            trs = dict_['ec']['word'][0]['trs']
            for i in trs:
                result.append(i['tr'][0]['l']['i'][0])
        return result

    @staticmethod
    def get_sentences(dict_):
        result = []
        if dict_.get('phrs'):
            for i in dict_['phrs']['phrs'][:3]:
                phr = i['phr']
                headword = phr['headword']['l']['i']
                tr = phr['trs'][0]['tr']['l']['i']
                result.append({'example': headword, 'translate': tr})
        return result


class IcibaSDK(BaseTranslateSDK):
    jp = 'ja'

    def __init__(
            self,
            session,
            trans_url="http://fy.iciba.com/ajax.php",
            interface_url="http://dict-mobile.iciba.com/interface/index.php",
            paraphrase_url="http://www.iciba.com/index.php"):
        self.session = session
        self.trans_url = trans_url
        self.interface_url = interface_url
        self.paraphrase_url = paraphrase_url

    async def interface(self,
                        word,
                        c="word",
                        m="getsuggest",
                        cilent=6,
                        is_need_mean=1,
                        nums=5):
        response = await self.session.get(
            self.interface_url,
            params={
                'c': c,
                'm': m,
                'nums': nums,
                'client': cilent,
                'is_need_mean': is_need_mean,
                'word': word
            })
        return response

    async def translate(self, word, a="fy", origin="auto", dest="auto"):
        origin, dest = self.trans_symbol(origin, dest)
        response = await self.session.get(
            self.trans_url, params={
                'a': a,
                'f': origin,
                't': dest,
                'w': word
            })
        return response

    @catch_req()
    async def paraphrase(self, word, a="getWordMean", c="search", dict_list=[8]):
        params = [('a', a), ('word', word), ('c', c)]
        for i in dict_list:
            params.append(('list', i))
        return await self.session.get(self.paraphrase_url, params=params)

    @staticmethod
    def get_means(d) -> list:
        parts = d[0]['parts']
        result = []
        for p in parts:
            means = '; '.join(p['means'])
            result.append(p['part'] + ' ' + means)
        return result

    @staticmethod
    def get_sentences(d):
        sentences = d.get('sentence', [])
        result = []
        for s in sentences:
            result.append({
                'example': s['Network_en'],
                'translate': s['Network_cn']
            })
        return result


class BingSDK(BaseTranslateSDK):
    def __init__(
            self,
            session,
            dict_url="https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/",
            trans_url="https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/",
    ):
        self.session = session
        self.dict_url = dict_url
        self.trans_url = trans_url

    @catch_req()
    async def paraphrase(self, words):
        return await self.session.get(
            self.dict_url, params={
                'q': words,
                'format': 'application/json'
            })

    @catch_req()
    async def translate(self, words: str):
        return await self.session.get(
            self.trans_url, params={
                'q': words.replace(' ', '+'),
                'format': 'application/json'
            }
        )
