import re
from asyncio import create_task

from nonebot import get_bot, get_driver

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
        user_id=next(iter(get_driver().config.superusers)),
        message=f"Exception {etype}: {emsg}",
        auto_escape=True,
    )
    for message in messages:
        await get_bot().send_private_msg(
            detail_type="private",
            user_id=next(iter(get_driver().config.superusers)),
            message=message,
            auto_escape=False,
        )


def send_exception_to_su(e, *messages):
    create_task(exception_to_su_real(e, *messages))
