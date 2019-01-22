import random
import string
import time

from linguister.exceptions import NotSupportLangException

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