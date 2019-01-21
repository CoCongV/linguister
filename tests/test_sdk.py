import asyncio

import aiohttp

from linguister import loop, generate_ph
from linguister.sdk import YouDaoSDK, IcibaSDK


class TestSDK:
    words = ['love', 'I love you']
    def test_youdao(self):
        future = asyncio.ensure_future(self.youdao())
        loop.run_until_complete(future)
    
    async def youdao(self):
        async with aiohttp.ClientSession() as session:
            for words in self.words:
                youdao_sdk = YouDaoSDK(session)
                response = await youdao_sdk.paraphrase(words)
                result = await response.json()
                ec_dict = result.get('ec')
                if ec_dict:
                    ph = generate_ph(ec_dict['word'][0].get('usphone'),
                                    ec_dict['word'][0].get('ukphone'))
                else:
                    ph = generate_ph()

                means = YouDaoSDK.get_mean_list(result)
                sentences = YouDaoSDK.get_sentences(result)
                response.release()
                return {
                    'ph': ph,
                    'means': means,
                    'sentences': sentences,
                    'source': 'youdao',
                    'audio': None,
                    'words': words
                }
    
    def test_iciba(self):
        future = asyncio.ensure_future(self.iciba())
        loop.run_until_complete(future)
    
    async def iciba(self):
        async with aiohttp.ClientSession() as session:
            for words in self.words:
                iciba_sdk = IcibaSDK(session)
                response = await iciba_sdk.paraphrase(words)
                result = await response.json()
                sentences = IcibaSDK.get_sentences(result)
                base_info = result['baesInfo']

                data = {'source': 'iciba'}
                audio = None
                ph = None
                if base_info.get('symbols'):
                    symbols = base_info['symbols']
                    ph = generate_ph(symbols[0].get('ph_am'), symbols[0].get('ph_en'))
                    audio = symbols[0].get('ph_am_mp3') or symbols[0].get('ph_en_mp3')
                    means = IcibaSDK.get_means(symbols)
                    data['means'] = means
                else:
                    ph = generate_ph()
                    data.update({
                        'translate_msg': base_info['translate_msg'],
                        'translate_result': base_info['translate_result']
                    })

                response.release()
                data.update({
                    'audio': audio,
                    'ph': ph,
                    'sentences': sentences,
                    'words': words
                })
                return data