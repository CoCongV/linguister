import asyncio
from functools import partial

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
from linguister.const import DEFAULT_USER_AGENT
from linguister.errout import err
from linguister.exceptions import ConfigException
from linguister.info import change_line, out
from linguister.__version__ import __version__

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()
conf = Config()
conf.load_toml()

is_play = False
def _callback_out(future: asyncio.Future, say=False):
    global is_play
    result = future.result()
    out(result)
    if say and not is_play and result.get('audio'):
        play(result['audio'])
        is_play = True

async def run(words, say, origin, dest, proxy):
    callback_out = partial(_callback_out, say=say)
    tasks = []
    conf.update({'proxy': proxy})
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(
            headers={'User-Agent': DEFAULT_USER_AGENT}, timeout=timeout) as session:
        for sdk in conf.SDKS:
            try:
                future = asyncio.Future()
                async_obj = getattr(main, sdk)(session, conf, future)
            except AttributeError as e:
                msg = "SDK Load Exception, sdk: {}, detail: {}".format(
                    sdk, str(e))
                err(msg)
                if conf.DEBUG:
                    raise ConfigException(msg)
                else:
                    continue
            else:
                future.add_done_callback(callback_out)
                task = asyncio.ensure_future(async_obj(words))
                tasks.append(task)

        await asyncio.gather(*tasks)
    change_line()

@click.group()
@click.version_option(prog_name="linguister", version=__version__)
def cli():
    pass

@cli.command()
@click.argument("words", nargs=-1, type=click.STRING, required=True)
@click.option("-s", "--say/--no-say", default=False, help="play audio")
@click.option("-o", "--origin", default="en", help="origin language")
@click.option("-d", "--dest", default="cn", help="destination language")
@click.option("-p", "--proxy", default=None, help="http or https proxy")
def translate(words, say, origin, dest, proxy):
    words = " ".join(words)
    future = asyncio.ensure_future(run(words, say, origin, dest, proxy))
    loop.run_until_complete(future)
    # Wait 250 ms for the underlying SSL connections to close
    loop.run_until_complete(asyncio.sleep(0.250))


@cli.command("generate-conf-file")
def generate_conf_file():
    config = Config()
    file_path = config.dump_toml()
    print(file_path)