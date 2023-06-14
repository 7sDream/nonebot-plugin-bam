import datetime
import hashlib
import itertools
import time
import urllib

from .api import APIResult


def get_token(url: str):
    return url.split("/").pop()[:-4]

def remove_chars(s, chars):
    s.translate({ ord(c): None for c in chars })

class WbiToken(APIResult):
    URL = "https://api.bilibili.com/x/web-interface/nav"

    KEY_ENC_TABLE = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52,
    ]

    def __init__(self):
        super().__init__()

    def __initialize__(self, body):
        self.date = datetime.date.today()
        wbi = body["data"]["wbi_img"]
        self.token = get_token(wbi["img_url"]) + get_token(wbi["sub_url"])

    def get_key(self) -> str:
        if not self.ok:
            return ""

        ''.join([self.token[i] for i in itertools.islice(self.KEY_ENC_TABLE, 32)])

    def add_signature(self, query: dict[str, str]):
        if not self.ok:
            return ""

        query["wts"] = str(round(time.time()))
        final = '&'.join([
            urllib.parse.quote_plus(k) + "=" + urllib.parse.quote_plus(remove_chars(v, "!'()*"))
            for k, v in sorted(query.items())
        ]) + self.get_key()
        query["w_rid"] = hashlib.md5(final.encode()).hexdigest()

_wbi_token = None

async def wbi_token() -> WbiToken:
    global _wbi_token

    if _wbi_token is None:
        _wbi_token = await WbiToken.of()
    if not _wbi_token.ok:
        _wbi_token = await WbiToken.of()
    if _wbi_token.date == datetime.date.today():
        return _wbi_token

    _wbi_token = None
    return await wbi_token()
