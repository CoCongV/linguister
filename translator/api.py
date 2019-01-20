import hashlib
from uuid import uuid4
from importlib import import_module
import os

from requests import Session


class YouDaoApi:
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