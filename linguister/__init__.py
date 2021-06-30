import asyncio
from asyncio import queues
from functools import partial

import click
import colorama
import httpx

from linguister import main
from linguister.audio import play
from linguister.config import Config
from linguister.const import DEFAULT_USER_AGENT
from linguister.errout import err
from linguister.exceptions import ConfigException
from linguister.info import change_line, err_out, out
from linguister.__version__ import __version__

colorama.init(autoreset=True)
loop = asyncio.get_event_loop()
wqueue = asyncio.Queue()
conf = Config()
conf.load_conf()


is_play = False
def output(result, say=False):
    global is_play
    if result.get("err"):
        err_out(result["err"])
        return
    else:
        out(result["some"])
    some = result["some"]
    if say and not is_play and some.get('audio'):
        play(some['audio']["us"])
        is_play = True

async def run(words, say, origin, dest, proxy):
    conf.update({'proxy': proxy})
    async with httpx.AsyncClient(headers={'User-Agent': DEFAULT_USER_AGENT}, timeout=10) as client:
        for sdk in conf.SDKS:
            try:
                future = asyncio.Future()
                async_obj: main.SDKRunner = getattr(main, sdk)(client, conf, future, wqueue)
            except AttributeError as e:
                msg = "SDK Load Exception, sdk: {}, detail: {}".format(
                    sdk, str(e))
                err(msg)
                if conf.DEBUG:
                    raise ConfigException(msg)
                else:
                    continue
            else:
                asyncio.ensure_future(async_obj(words))

        i = 0
        while i < len(conf.SDKS):
            i += 1
            output(await wqueue.get(), say)

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