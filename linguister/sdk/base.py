from functools import partial
import random
import string
import time

from httpx import AsyncClient

from linguister.exceptions import NotSupportLangException

class BaseTranslateSDK:
    zh = 'zh' # China
    en = 'en' # English
    jp = 'jp' # Japan
    de = 'de' # German
    fr = 'fr' # France
    es = 'es' # Spain

    def __init__(self, client: AsyncClient, proxy=None):
        self.client = client
        self.proxy = proxy
        self._get = partial(self.client.get)

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
    
    def get_means(self, *args, **kwargs) -> list:
        pass