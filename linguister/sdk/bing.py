from linguister.exceptions import catch_req
from linguister.sdk import BaseTranslateSDK


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