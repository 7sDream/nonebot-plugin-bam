import re
import random
import operator

from nonebot.adapters.cqhttp import Bot, Event, Message
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE
from nonebot.log import logger
from nonebot.rule import regex, to_me
from nonebot import on_command, on_message

from .bilibili.activity import activity, H5Activity

from .common import G_CONF, SEP, RE_NUMBER

cmd_bilibili_activity_info = on_command(
    SEP.join(["bam", "act"]), rule=to_me(), permission=GROUP | PRIVATE, block=True
)


@cmd_bilibili_activity_info.handle()
async def bilibili_activity_info(bot: Bot, event: Event, state: dict):
    messages = []

    if await GROUP(bot, event):
        messages.append(f"[CQ:at,qq={event.user_id}]")

    args = str(event.message).strip()

    if RE_NUMBER.match(args) is None:
        messages.append("参数错误，请输入正确的动态 ID")
        return await cmd_bilibili_activity_info.finish("\n".join(messages))

    act_id = int(args)

    act = await activity(act_id)

    if act is None:
        messages.append("获取动态信息失败")
        return await cmd_bilibili_activity_info.finish("\n".join(messages))

    username = getattr(act, "username", f"ID 为 {act.uid} 的用户")
    messages.extend([f"{username} 的动态", "", act.display()])

    h5_share_card = None
    if isinstance(act, H5Activity):
        h5_share_card = act.h5_share_card()

    if h5_share_card is not None:
        await cmd_bilibili_activity_info.send(Message("\n".join(messages)))
        await cmd_bilibili_activity_info.finish(Message(h5_share_card))
    else:
        await cmd_bilibili_activity_info.finish(Message("\n".join(messages)))
