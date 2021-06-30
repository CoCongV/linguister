import asyncio

import httpx

from linguister import loop
from linguister.utils import generate_ph
from linguister.sdk import YouDaoSDK


class TestSDK:
    words = ['love', 'I love you']
    def test_youdao(self):
        future = asyncio.ensure_future(self.youdao())
        loop.run_until_complete(future)

    async def youdao(self):
        results = []
        async with httpx.AsyncClient() as client:
            for words in self.words:
                youdao_sdk = YouDaoSDK(client)
                response = await youdao_sdk.paraphrase(words)
                result = response.json()
                ec_dict = result.get('ec')
                if ec_dict:
                    ph = generate_ph(
                        US=ec_dict['word'][0].get('usphone'),
                        UK=ec_dict['word'][0].get('ukphone'))
                else:
                    ph = generate_ph()

                means = YouDaoSDK.get_means(result)
                sentences = YouDaoSDK.get_sentences(result)
                results.append(
                {
                    'ph': ph,
                    'means': means,
                    'sentences': sentences,
                    'source': 'youdao',
                    'audio': None,
                    'words': words
                })
        return results
                