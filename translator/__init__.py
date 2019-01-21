import asyncio
from multiprocessing import Process

import aiohttp
from aiohttp.client_exceptions import ClientError
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass
import click
import colorama

from translator.exceptions import TranslatorException
from translator.sdk import IcibaSDK, YouDaoSDK
from translator.info import change_line, out
from translator.audio import play

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()

def generate_ph(en=None, us=None):
    if not en:
        en = str([])
    else:
        en = str([en])
    if not us:
        us = str([])
    else:
        us = str([us])
    return 'US ' + us + ' UK ' + en

async def iciba(words, session):
    iciba_sdk = IcibaSDK(session)
    try:
        response = await iciba_sdk.paraphrase(words)
    except (TranslatorException, ClientError) as e:
        return {'source': 'iciba', 'exc': e}
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

async def youdao(words, session):
    youdao_sdk = YouDaoSDK(session)

    try:
        response = await youdao_sdk.paraphrase(words)
    except (TranslatorException, ClientError) as e:
        return {'source': 'youdao', 'exc': e}

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


async def run(words, say):
    tasks = []
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(iciba(words, session))
        tasks.append(task)

        task = asyncio.ensure_future(youdao(words, session))
        tasks.append(task)

        responses = await asyncio.gather(*tasks)
    change_line()

    audio = None
    for res in responses:
        out(res)
        if say:
            if not audio:
                if res.get('audio'):
                    audio = res['audio']
    if audio:
        play(audio)

@click.command()
@click.argument('words', nargs=-1, type=click.STRING)
@click.option('-s', '--say', default=False, help="play audio", type=click.BOOL)
def cli(words, say=True):
    words = ' '.join(words)

    future = asyncio.ensure_future(run(words, say))
    loop.run_until_complete(future)
