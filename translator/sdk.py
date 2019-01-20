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
                 app_id,
                 app_key,
                 url="https://openapi.youdao.com/api",
                 voice_type=0,
                 ext="mp3",
                 from_lang="auto",
                 to_lang="auto",
                 session=Session()):
        self.app_key = app_key
        self.app_id = app_id
        self.url = url
        self.voice_type = voice_type
        self.ext = ext
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.session = session

    def translate(self, text, from_lang=None, to_lang=None, ext=None, voice_type=None):
        sign, salt = self.generate_sign(text)
        response = self.session.get(
            self.url,
            params={
                "q": text,
                "from": from_lang or self.from_lang,
                "to": to_lang or self.to_lang,
                "appKey": self.app_id,
                "salt": salt,
                "sign": sign,
                "ext": ext or self.ext,
                "voice": voice_type or self.voice_type
            })
        return response

    def generate_sign(self, text):
        salt = str(uuid4())
        m = hashlib.md5()
        m.update(''.join((self.app_id, text, salt, self.app_key)).encode())
        return m.hexdigest(), salt


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
