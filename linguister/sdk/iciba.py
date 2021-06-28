from httpx import Response

from linguister.exceptions import catch_req
from linguister.sdk import BaseTranslateSDK


LANGUAGES = {
    'ja': 'japanese',
    'en': 'english',
}
LANGCODES = dict(map(reversed, LANGUAGES.items()))


class IcibaSDK(BaseTranslateSDK):
    # API Address: https://github.com/shichunlei/-Api/blob/master/KingsoftDic.md
    jp = 'ja'

    def __init__(
            self,
            session,
            trans_url="http://fy.iciba.com/ajax.php",
            interface_url="http://dict-mobile.iciba.com/interface/index.php",
            # paraphrase_url="http://www.iciba.com/index.php",
            proxy=None):
        super().__init__(session, proxy)
        self.trans_url = trans_url
        self.interface_url = interface_url
        # self.paraphrase_url = paraphrase_url

    async def interface(self, word):
        response = await self._get(
            self.interface_url,
            params={
                'c': "word",
                'm': "getsuggest",
                'nums': 5,
                'client': 6,
                'is_need_mean': 1,
                'word': word
            })
        return response

    async def translate(self, word, a="fy", origin="auto", dest="auto"):
        origin, dest = self.trans_symbol(origin, dest)
        response = await self._get(
            self.trans_url, params={
                'a': a,
                'f': origin,
                't': dest,
                'w': word
            })
        return response

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