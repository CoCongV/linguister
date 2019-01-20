import asyncio
from multiprocessing import Process

import aiohttp
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass
import click
import colorama

from translator.sdk import IcibaSDK, YouDaoSDK
from translator.sysout import (info_out, mean_out, sentence_out, change_line,
                               translate_out, separator)
from translator.audio import play

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()

def generate_ph(en, us):
    if not en:
        en = str([])
    else:
        en = str([en])
    if not us:
        us = str([])
    else:
        us = str([us])
    return 'US ' + us + ' EN ' + en

async def iciba(words, session):
    change_line()
    iciba_sdk = IcibaSDK(session)
    response = await iciba_sdk.paraphrase(words)
    result = await response.json()
    sentence = result.get('sentence', [])
    base_info = result['baesInfo']

    audio_file = None
    if base_info.get('symbols'):
        symbols = base_info['symbols']
        ph = generate_ph(symbols[0].get('ph_am'), symbols[0].get('ph_en'))
        info_out(words, ph, 'iciba.com')
        audio_file = symbols[0].get('ph_am_mp3') or symbols[0].get('ph_en_mp3')

        for part in symbols[0]['parts']:
            mean_out(part['part'], part['means'])
    else:
        info_out(words, '', 'iciba.com')
        translate_out(base_info['translate_msg'], base_info['translate_result'])

    change_line()
    for n, s in enumerate(sentence, start=1):
        sentence_out(n, s['Network_en'], s['Network_cn'])
    response.release()
    separator()
    return audio_file

async def youdao(words, session):
    youdao_sdk = YouDaoSDK(session)
    response = await youdao_sdk.paraphrase(words)
    result = await response.json()
    ec_dict = result['ec']
    ph = generate_ph(ec_dict['word'][0].get('usphone'),
                     ec_dict['word'][0].get('ukphone'))
    info_out(words, ph, 'youdao.com')
    mean_list = YouDaoSDK.generate_trans_list(result)
    for mean in mean_list:
        mean_out('', mean)
    sentences = YouDaoSDK.generate_sentences(result)
    for n, i in enumerate(sentences, start=1):
        sentence_out(n, i['headword'], i['tr'])
    separator()
    return None

async def run(words, say):
    tasks = []
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(iciba(words, session))
        tasks.append(task)

        task = asyncio.ensure_future(youdao(words, session))
        tasks.append(task)

        responses = await asyncio.gather(*tasks)
    if say:
        for audio_file in responses:
            if audio_file:
                play(audio_file)

@click.command()
@click.argument('words', nargs=-1, type=click.STRING)
@click.option('-s', '--say', default=False, help="play audio", type=click.BOOL)
def cli(words, say=True):
    words = ' '.join(words)

    future = asyncio.ensure_future(run(words, say))
    loop.run_until_complete(future)
