from urllib.parse import urlencode

from linguister.exceptions import catch_req
from . import BaseTranslateSDK


class YouDaoSDK(BaseTranslateSDK):
    """
    app_key: Application key
    app_id : Application ID
    """

    def __init__(self,
                 session,
                 suggest_url='http://dict.youdao.com/suggest',
                 paraphrase_url="http://dict.youdao.com/jsonapi",
                 translate_url="http://fanyi.youdao.com/translate",
                 proxy=None):
        super().__init__(session)
        self.suggest_url = suggest_url
        self.paraphrase_url = paraphrase_url
        self.translate_url = translate_url

    async def interface(self, word, lang='eng', num=5, doctype='json'):
        return await self._get(
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
        return await self._get(
            self.paraphrase_url + '?' + params)

    @staticmethod
    def get_means(dict_):
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