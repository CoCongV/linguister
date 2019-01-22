from functools import wraps

from aiohttp.client_exceptions import ClientConnectionError

def catch_req(content_type='json'):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            if response.status != 200:
                raise RequestException("Request Error: {}".format(response.status))
            else:
                if content_type == 'json':
                    result = await response.json()
                    if result.get('errno'):
                        raise RequestException(
                            "Request Error: errmsg: {}, errcode: {}".format(
                                result.get('errmsg'), result.get('errno')))
                return response

        return wrapper
    return decorator


class LinguisterException(Exception):
    pass


class RequestException(LinguisterException):
    def __init__(self, message="Request Error"):
        super().__init__(message)

class NotSupportLangException(LinguisterException):
    def __init__(self, message='Not support this language'):
        super().__init__(message)


class SymbolException(LinguisterException):
    def __init__(self,
                 message="Don't supported this language or symbol error"):
        super().__init__(message)
