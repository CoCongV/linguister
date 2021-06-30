from re import template
from sys import prefix
from urllib.parse import urlencode

from linguister.exceptions import catch_req
from linguister.utils import generate_temp
from . import BaseTranslateSDK, SentencesResults


class YouDaoSDK(BaseTranslateSDK):
    """
    app_key: Application key
    app_id : Application ID
    """
    CAN_PLAY = True

    def __init__(self,
                 client,
                 suggest_url='http://dict.youdao.com/suggest',
                 paraphrase_url="http://dict.youdao.com/jsonapi",
                 translate_url="http://fanyi.youdao.com/translate",
                 voice_url="http://dict.youdao.com/dictvoice?type={type}&audio={word}",
                 proxy=None):
        super().__init__(client)
        self.suggest_url = suggest_url
        self.paraphrase_url = paraphrase_url
        self.translate_url = translate_url
        self.voice_url = voice_url

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
                             "simple",
                             "phrs",                             
                         ], "fanyi"],
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
            self.paraphrase_url, params=params)

    @staticmethod
    def get_means(dict_):
        result = []
        if dict_.get('ec'):
            trs = dict_['ec']['word'][0]['trs']
            for i in trs:
                result.append(i['tr'][0]['l']['i'][0])
        return result

    @staticmethod
    def get_sentences(dict_) -> SentencesResults:
        result = []
        if dict_.get('phrs'):
            for i in dict_['phrs']['phrs'][:3]:
                phr = i['phr']
                headword = phr['headword']['l']['i']
                tr = phr['trs'][0]['tr']['l']['i']
                result.append({'example': headword, 'translate': tr})
        return result

    
    async def _download_autio(self, word, type=0): 
        # http://www.cxyzjd.com/article/q6q6q/109342595
        # 0 is US voice
        # 1 is UK voice
        return await self._get(self.voice_url.format(type=type, word=word))

    async def generate_voice(self, word):
        us_response = await self._download_autio(word, 0)
        us_filename = generate_temp(us_response.content, prefix="youdao_us")

        uk_response = await self._download_autio(word, 1)
        uk_filename = generate_temp(uk_response.content, prefix="youdao_uk")
        
        return {"us": us_filename, "uk": uk_filename}
