from aiohttp.client_exceptions import ClientError

from linguister.exceptions import LinguisterException, RequestException
from linguister.sdk import IcibaSDK, YouDaoSDK, BingSDK, GoogleSDK
from linguister.utils import generate_ph


async def iciba(words, session):
    iciba_sdk = IcibaSDK(session)
    try:
        response = await iciba_sdk.paraphrase(words)
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
        "words": words
    })
    return data

async def youdao(words, session):
    youdao_sdk = YouDaoSDK(session)

    try:
        response = await youdao_sdk.paraphrase(words)
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
        "words": words
    }

async def bing(words, session):
    bing_sdk = BingSDK(session)

    try:
        response = await bing_sdk.paraphrase(words)
    except (LinguisterException, ClientError) as e:
        return {"source": "bing", "exc": e}

    # result = await response.json()
    print(await response.text())

async def google(words, session):
    google_sdk = GoogleSDK(session)
    result = await google_sdk.translate(words)
    ph = generate_ph(
        Origin=result['pronunciation'],
        Dest=result['extra_data']['translation'][1][-1])

    return {
        'words': words,
        'audio': None,
        'source': 'Google',
        'ph': ph,
        'sentences': google_sdk.get_sentences(result),
        'means': google_sdk.get_means(result)
    }
