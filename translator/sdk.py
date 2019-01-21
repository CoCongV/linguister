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

import requests
from requests import Session


class BaseTranslateSDK:

    def generate_random_str(self, length=24) -> str:
        return ''.join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(24))

    def generate_timestamp(self) -> int:
        return int(time.time())


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

    async def suggest(self, word, lang='eng', num=5, doctype='json'):
        return await self.session.get(
            self.suggest_url,
            params={
                'q': word,
                'le': lang,
                'num': num,
                'doctype': doctype
            })

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


class QQSDK(BaseTranslateSDK):

    def __init__(self,
                 app_id: int,
                 app_key: str,
                 trans_url="https://api.ai.qq.com/fcgi-bin/nlp/nlp_texttranslate",
                 wordsync_url = 'https://api.ai.qq.com/fcgi-bin/nlp/nlp_wordsyn',
                 session=Session()):
        self.app_id = app_id
        self.app_key = app_key
        self.default_source = 'en'
        self.default_target = 'zh'
        self.session = session
        self.trans_url = trans_url

    def translate(self, text, app_id=None, app_key=None, source=None, target=None):
        time_stamp = self.generate_timestamp()
        nonce_str = self.generate_random_str()
        params = {
                'app_id': app_id or self.app_id,
                'time_stamp': time_stamp,
                'nonce_str': nonce_str,
                'text': text,
            }
        sign = self.generate_sign(dict(params), app_key
                                  or self.app_key).upper()
        params['sign'] = sign

        trans_params = dict(params)
        trans_params.update({
            'source': source or self.default_source,
            'target': target or self.default_target
        })
        trans_res = self.translate(trans_params)
        return trans_res

    def generate_sign(self, params: dict, app_key=None):
        params = OrderedDict(sorted(params.items()))
        m = hashlib.md5()
        value = urlencode(params) + "&app_key=" + app_key
        m.update(value.encode())
        return m.hexdigest()


    def _translate(self, params):
        response = self.session.get(
            self.trans_url,
            params=params)
        return response


class IcibaSDK(BaseTranslateSDK):

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

    @staticmethod
    def catch_req():
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                if response.status_code == 200:
                    return response.json(), True
                else:
                    return response.status_code, False

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

    async def translate(self, word, a="fy", from_="auto", to="auto"):
        response = await self.session.get(
            self.trans_url, params={
                'a': a,
                'f': from_,
                't': to,
                'w': word
            })
        return response

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
