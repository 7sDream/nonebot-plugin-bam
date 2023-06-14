import abc
import time
import urllib
from http.cookies import SimpleCookie

from aiohttp import ClientSession, ClientTimeout, CookieJar, TCPConnector
from nonebot import get_driver
from nonebot.log import logger

client: ClientSession = None

LOGNAME = "BILIBILI:API"


async def init_client():
    global client
    if client is not None:
        return

    cookie = CookieJar()
    cookie.update_cookies(SimpleCookie("PVID=2; Domain=live.bilibili.com; Path=/;"))

    timeout = ClientTimeout(total=3)

    client = ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
        },
        cookie_jar=cookie,
        timeout=timeout,
        connector=TCPConnector(force_close=True),
    )

    logger.success(f"[{LOGNAME}] init HTTP client ok")


class APIResult(abc.ABC):
    URL = None

    def __init__(self):
        self.ok = False

    @abc.abstractmethod
    def __initialize__(self, body, **params):
        pass

    @classmethod
    async def of(cls, **params):
        instance = cls()
        params["ts"] = str(time.time())
        try:
            url = cls.URL.format(**params)
            if hasattr(cls, "QUERY"):
                query = {k: v.format(**params) for k, v in cls.QUERY.items()}
                if getattr(cls, "WBI", False):
                    from .wbi import wbi_token
                    token = await wbi_token()
                    token.add_signature(query)
                url += '?' + urllib.parse.urlencode(query)
            logger.info(f"[{LOGNAME}] request: {url}")
            async with client.get(url) as resp:
                logger.debug(f"[{LOGNAME}:{cls.__name__}] {url}: response {resp}")
                data = await resp.json()
                logger.debug(f"[{LOGNAME}:{cls.__name__}] {url}: body {data}")
                try:
                    del params["ts"]
                    instance.__initialize__(data, **params)
                except Exception as e:
                    instance.ok = False
                    logger.info(
                        f"[{LOGNAME}:{cls.__name__}] {url} {type(e).__name__} {repr(e)}, response json {data}"
                    )
        except Exception as e:
            logger.info(
                f"[{LOGNAME}:{cls.__name__}] request failed {type(e).__name__}: {repr(e)}"
            )
        return instance


get_driver().on_startup(init_client)
