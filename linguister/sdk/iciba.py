from httpx import Response

from linguister.exceptions import catch_req
from linguister.sdk import BaseTranslateSDK


LANGUAGES = {
    'ja': 'japanese',
    'en': 'english',
}
LANGCODES = dict(map(reversed, LANGUAGES.items()))


class IcibaSDK(BaseTranslateSDK):
    jp = 'ja'

    def __init__(
            self,
            session,
            trans_url="http://fy.iciba.com/ajax.php",
            interface_url="http://dict-mobile.iciba.com/interface/index.php",
            paraphrase_url="http://www.iciba.com/index.php",
            proxy=None):
        super().__init__(session, proxy)
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
        response = await self._get(
            self.interface_url,
            params={
                'c': c,
                'm': m,
                'nums': nums,
                'client': cilent,
                'is_need_mean': is_need_mean,
                'word': word
            },
            proxy=self.proxy)
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

    @catch_req()
    async def paraphrase(self, word, a="getWordMean", c="search", dict_list=[8]) -> Response:
        params = [('a', a), ('word', word), ('c', c)]
        for i in dict_list:
            params.append(('list', i))
        return await self._get(
            self.paraphrase_url, params=params)

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