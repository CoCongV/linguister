import asyncio

import aiohttp
from aiohttp.client_exceptions import ClientError
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass
import click
import colorama

from linguister import main
from linguister.audio import play
from linguister.config import Config
from linguister.errout import err
from linguister.exceptions import ConfigException
from linguister.info import change_line, out
from linguister.const import DEFAULT_USER_AGENT

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()
conf = Config()
conf.load_toml()

async def run(words, say, origin, dest):
    tasks = []
    async with aiohttp.ClientSession(headers=DEFAULT_USER_AGENT) as session:
        for sdk in conf.SDKS:
            try:
                async_func = getattr(main, sdk)
            except AttributeError as e:
                msg = "SDK Load Exception, sdk: {}, detail: {}".format(
                    sdk, str(e))
                err(msg)
                if conf.DEBUG:
                    raise ConfigException(msg)
                else:
                    continue
            task = asyncio.ensure_future(async_func(words, session))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
    change_line()

    audio = None
    for res in responses:
        if res:
            out(res)
        if say and res:
            if not audio:
                if res.get("audio"):
                    audio = res["audio"]
    if audio:
        play(audio)

@click.group()
def cli():
    pass

@cli.command()
@click.argument("words", nargs=-1, type=click.STRING, required=True)
@click.option("-s", "--say/--no-say", default=False, help="play audio")
@click.option("-o", "--origin", default="en", help="origin language")
@click.option("-d", "--dest", default="cn", help="destination language")
def translate(words, say, origin, dest):
    words = " ".join(words)

    future = asyncio.ensure_future(run(words, say, origin, dest))
    loop.run_until_complete(future)


@cli.command("generate-conf-file")
def generate_conf_file():
    config = Config()
    file_path = config.dump_toml()
    print(file_path)