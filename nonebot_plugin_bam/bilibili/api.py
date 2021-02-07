import asyncio
from aiohttp import ClientSession, CookieJar, ClientTimeout, TCPConnector
from http.cookies import SimpleCookie
import abc
import time

from nonebot.log import logger

from ..common import DRIVER

client: ClientSession = None

LOGNAME = "BILIBILI:API"


async def init_client():
    global client
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

    logger.info(f"[{LOGNAME}] Client initalited")


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
            logger.info(f"[{LOGNAME}] request: {url}")
            async with client.get(url) as resp:
                data = await resp.json()
                try:
                    del params["ts"]
                    instance.__initialize__(data, **params)
                except Exception as e:
                    instance.ok = False
                    logger.warning(
                        f"[{LOGNAME}:{cls.__name__}] {url} {type(e).__name__} {repr(e)}, response json {data}"
                    )
        except Exception as e:
            logger.warning(
                f"[{LOGNAME}:{cls.__name__}] request failed {type(e).__name__}: {repr(e)}"
            )
        return instance


DRIVER.on_startup(init_client)
