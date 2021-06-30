from abc import ABC, abstractmethod
from asyncio import Queue, Future
from typing import Any, Callable, TypedDict, Union

from httpx import AsyncClient
from httpx._exceptions import HTTPError

from linguister.exceptions import LinguisterException, RequestException
from linguister.sdk import IcibaSDK, YouDaoSDK, BingSDK, GoogleSDK
from linguister.utils import generate_ph


class Some(TypedDict):
    ph: any
    means: any
    sentences: any
    source: str
    audio: Union[dict[str, str], None]
    word: str


class Err(TypedDict):
    source: str
    exc: Exception


class Result(TypedDict):
    some: Union[Some, None]
    err: Union[Err, None]


class SDKRunner(ABC):

    def __init__(self, client: AsyncClient, conf, future: Future, wq: Queue):
        self.client = client
        self.conf = conf
        self.future = future
        self.wqueue = wq
    
    async def __call__(self, word):
        await self.wqueue.put(await self.run(word))
    
    @abstractmethod
    async def run(self, word):
        pass

# Deprecation
class Iciba(SDKRunner):

    async def run(self, words) -> Result:
        iciba_sdk = IcibaSDK(self.client, proxy=self.conf.proxy)
        try:
            response = await iciba_sdk.paraphrase(words)
            result = response.json()
            if result.get('errno'):
                raise RequestException(
                    "Request Error: errmsg: {}, errcode: {}".format(
                        result.get('errmsg'), result.get('errno')))
        except (LinguisterException, HTTPError) as e:
            err = {"source": "iciba", "exc": e}
            return {"some": None, "err": err}
        sentences = IcibaSDK.get_sentences(result)
        base_info = result["baesInfo"]

        data = {"source": "iciba"}
        audio = None
        ph = None
        if base_info.get("symbols"):
            symbols = base_info["symbols"]
            ph = generate_ph(US=symbols[0].get("ph_am"), UK=symbols[0].get("ph_en"))
            audio = symbols[0].get("ph_am_mp3") or symbols[0].get("ph_en_mp3")
            means = IcibaSDK.get_means(symbols)
            data["means"] = means
        else:
            ph = generate_ph()
            data.update({
                "translate_msg": base_info["translate_msg"],
                "translate_result": base_info["translate_result"]
            })

        data.update({
            "audio": audio,
            "ph": ph,
            "sentences": sentences,
            "words": words
        })
        return {"some": data, "err": None}


class Youdao(SDKRunner):
    async def run(self, word):
        youdao_sdk = YouDaoSDK(self.client)

        try:
            response = await youdao_sdk.paraphrase(word)
        except (LinguisterException, HTTPError) as e:
            err = {"source": "youdao", "exc": e}
            return {"some": None, "err": err}

        result = response.json()
        ec_dict = result.get("ec")
        if ec_dict:
            ph = generate_ph(US=ec_dict["word"][0].get("usphone"),
                            UK=ec_dict["word"][0].get("ukphone"))
        else:
            ph = generate_ph()

        means = YouDaoSDK.get_means(result)
        sentences = YouDaoSDK.get_sentences(result)
        voice = await youdao_sdk.generate_voice(word)
        
        data = {
            "ph": ph,
            "means": means,
            "sentences": sentences,
            "source": "youdao",
            "audio": voice,
            "words": word
        }
        return {"some": data, "err": None}

async def bing(words, session, client_args):
    # TODO:
    bing_sdk = BingSDK(session)

    try:
        response = await bing_sdk.paraphrase(words)
    except (LinguisterException, HTTPError) as e:
        return {"source": "bing", "exc": e}

    # result = await response.json()
    print(await response.text())


class Google(SDKRunner):

    async def __call__(self, words):
        google_sdk = GoogleSDK(self.client, proxy=self.conf.proxy)
        result = await google_sdk.translate(words)
        ph = generate_ph(
            Origin=result['pronunciation'],
            Dest=result['extra_data']['translation'][1][-1])

        data = {
            'words': words,
            'audio': None,
            'source': 'Google',
            'ph': ph,
            'sentences': google_sdk.get_sentences(result),
            'means': google_sdk.get_means(result)
        }
        self.future.set_result(data)
