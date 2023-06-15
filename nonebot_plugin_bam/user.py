from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .bilibili.user import user_info
from .common import RE_NUMBER
from .database import helper

cmd_user_fetch = on_command(
    ("bam", "user", "fetch"), rule=to_me(), permission=SUPERUSER
)


@cmd_user_fetch.handle()
async def user_fetch(event: MessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()

    if RE_NUMBER.match(arg_text):
        uid = int(arg_text)

        await cmd_user_fetch.send(user_id=event.user_id, message=f"开始获取 {uid} 用户信息")

        user = await user_info(uid)

        if user.ok:
            helper.add_user(uid, user.nickname, user.rid)
            await cmd_user_fetch.finish(
                f"UID: {uid}, 昵称: {user.nickname}, 直播间: {user.rid}, 已储存/更新完成。"
            )
        else:
            await cmd_user_fetch.finish(f"获取用户信息失败")
    else:
        await cmd_user_fetch.finish(f"UID 无效")
