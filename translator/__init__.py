import asyncio

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

async def iciba(word, session, say=False):
    iciba_sdk = IcibaSDK(session)
    # paraphrase
    response = await iciba_sdk.paraphrase(word)
    result = await response.json()
    sentence = result['sentence']
    base_info = result['baesInfo']
    symbols = base_info['symbols']
    info_out(word, symbols[0]['ph_am'], 'iciba.com')

    if say:
        play(symbols[0]['ph_en_mp3'])

    for part in symbols[0]['parts']:
        means_out(part['part'], part['means'])
    change_line()
    for id_, s in enumerate(sentence, start=1):
        sentence_out(id_, s['Network_en'], s['Network_cn'])

    response.release()


async def run(word, say):
    tasks = []
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(iciba(word, session, say))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)

@click.command()
@click.argument('word')
@click.option('-s', '--say', default=False, help="play audio")
def cli(word, say):
    print('')
    future = asyncio.ensure_future(run(word, True))
    loop.run_until_complete(future)
