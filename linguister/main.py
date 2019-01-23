from abc import ABC, abstractmethod

from aiohttp.client_exceptions import ClientError

from linguister.exceptions import LinguisterException, RequestException
from linguister.sdk import IcibaSDK, YouDaoSDK, BingSDK, GoogleSDK
from linguister.utils import generate_ph


class SDKRunner(ABC):

    def __init__(self, words, session, conf):
        self.words = words
        self.session = session
        self.conf = conf
    
    @abstractmethod
    async def __call__(self):
        pass

class Iciba(SDKRunner):

    async def __call__(self):
        iciba_sdk = IcibaSDK(self.session, proxy=self.conf.proxy)
        try:
            response = await iciba_sdk.paraphrase(self.words)
            result = await response.json()
            if result.get('errno'):
                raise RequestException(
                    "Request Error: errmsg: {}, errcode: {}".format(
                        result.get('errmsg'), result.get('errno')))
        except (LinguisterException, ClientError) as e:
            return {"source": "iciba", "exc": e}
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

        response.release()
        data.update({
            "audio": audio,
            "ph": ph,
            "sentences": sentences,
            "words": self.words
        })
        return data

class Youdao(SDKRunner):
    async def __call__(self):
        youdao_sdk = YouDaoSDK(self.session)

        try:
            response = await youdao_sdk.paraphrase(self.words)
        except (LinguisterException, ClientError) as e:
            return {"source": "youdao", "exc": e}

        result = await response.json()
        ec_dict = result.get("ec")
        if ec_dict:
            ph = generate_ph(US=ec_dict["word"][0].get("usphone"),
                            UK=ec_dict["word"][0].get("ukphone"))
        else:
            ph = generate_ph()

        means = YouDaoSDK.get_means(result)
        sentences = YouDaoSDK.get_sentences(result)
        response.release()
        return {
            "ph": ph,
            "means": means,
            "sentences": sentences,
            "source": "youdao",
            "audio": None,
            "words": self.words
        }

async def bing(words, session, aiohttp_args):
    # TODO:
    bing_sdk = BingSDK(session)

    try:
        response = await bing_sdk.paraphrase(words)
    except (LinguisterException, ClientError) as e:
        return {"source": "bing", "exc": e}

    # result = await response.json()
    print(await response.text())


class Google(SDKRunner):

    async def __call__(self):
        google_sdk = GoogleSDK(self.session, proxy=self.conf.proxy)
        result = await google_sdk.translate(self.words)
        ph = generate_ph(
            Origin=result['pronunciation'],
            Dest=result['extra_data']['translation'][1][-1])

        return {
            'words': self.words,
            'audio': None,
            'source': 'Google',
            'ph': ph,
            'sentences': google_sdk.get_sentences(result),
            'means': google_sdk.get_means(result)
        }
