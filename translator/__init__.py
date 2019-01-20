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

from translator.sdk import IcibaSDK
from translator.sysout import info_out, means_out, sentence_out, change_line
from translator.audio import play

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()

async def iciba(words, session):
    change_line()
    iciba_sdk = IcibaSDK(session)
    response = await iciba_sdk.paraphrase(words)
    result = await response.json()
    sentence = result['sentence']
    base_info = result['baesInfo']
    if base_info.get('symbols'):
        symbols = base_info['symbols']
        info_out(words, symbols[0]['ph_am'], 'iciba.com')
        audio_file = symbols[0]['ph_am_mp3']

        for part in symbols[0]['parts']:
            means_out(part['part'], part['means'])
    else:
        info_out(words, '', 'iciba.com')
        means_out('', base_info['translate_result'])
        
    change_line()
    for id_, s in enumerate(sentence, start=1):
        sentence_out(id_, s['Network_en'], s['Network_cn'])
    response.release()
    return None

async def run(words, say):
    tasks = []
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(iciba(words, session))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
    if say:
        for audio_file in responses:
            if audio_file:
                play(audio_file)

@click.command()
@click.argument('words', nargs=-1, type=click.STRING)
@click.option('-s', '--say', default=False, help="play audio", type=click.BOOL)
def cli(words, say):
    words = ' '.join(words)
        
    future = asyncio.ensure_future(run(words, say))
    loop.run_until_complete(future)
