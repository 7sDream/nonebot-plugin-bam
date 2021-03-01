import re
from asyncio import create_task

import nonebot
from nonebot.adapters.cqhttp import Bot

from .config import Config

DRIVER = G_CONF = SEP = CONF = None
try:
    DRIVER = nonebot.get_driver()
    G_CONF = DRIVER.config
    SEP = next(iter(G_CONF.command_sep))
    CONF = Config(**G_CONF.dict())
except ValueError:
    pass


def get_bot() -> Bot:
    for bot in DRIVER.bots.values():
        return bot
    return None


# Common regexes

RE_NUMBER = re.compile(r"^\d+$")

# Common functions


def cq_encode(s: str) -> str:
    s = s.replace("&", "&amp;")
    s = s.replace("[", "&#91;")
    s = s.replace("]", "&#93;")
    return s.replace(",", "&#44;")


async def exception_to_su_real(e, *messages):
    etype = type(e).__name__
    emsg = getattr(e, "message", repr(e))
    await get_bot().send_private_msg(
        user_id=next(iter(G_CONF.superusers)),
        message=f"Exception {etype}: {emsg}",
        auto_escape=True,
    )
    for message in messages:
        await get_bot().send_private_msg(
            user_id=next(iter(G_CONF.superusers)),
            message=message,
            auto_escape=False,
        )


def send_exception_to_su(e, *messages):
    create_task(exception_to_su_real(e, *messages))
