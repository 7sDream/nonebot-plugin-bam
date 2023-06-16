import re
from asyncio import create_task
from typing import Optional, cast

from nonebot import get_bot, get_driver
from nonebot.adapters.onebot.v11 import Bot

# Common regexes

RE_NUMBER = re.compile(r"^\d+$")

# Common functions

def try_get_bot() -> Optional[Bot]:
    try:
        bot = cast(Bot, get_bot())
    except ValueError:
        bot = None
    return bot

def cq_encode(s: str) -> str:
    s = s.replace("&", "&amp;")
    s = s.replace("[", "&#91;")
    s = s.replace("]", "&#93;")
    return s.replace(",", "&#44;")


async def exception_to_su_real(e, *messages):
    etype = type(e).__name__
    emsg = getattr(e, "message", repr(e))
    bot = try_get_bot()
    suid = 0
    for uid in get_driver().config.superusers:
        suid = int(uid)
    if bot is not None and suid != 0:
        await bot.send_private_msg(
            user_id=suid,
            message=f"Exception {etype}: {emsg}",
            auto_escape=True,
        )
        for message in messages:
            await bot.send_private_msg(
                user_id=suid,
                message=message,
                auto_escape=False,
            )


def send_exception_to_su(e, *messages):
    create_task(exception_to_su_real(e, *messages))
