from nonebot.adapters.cqhttp import Bot, Event
from nonebot.permission import SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE
from nonebot.rule import to_me
from nonebot import get_driver, on_command

from .common import G_CONF, SEP, RE_NUMBER
from .database import helper
from .bilibili.user import user_info

cmd_user_fetch = on_command(
    SEP.join(["bam", "user", "fetch"]), rule=to_me(), permission=SUPERUSER
)


@cmd_user_fetch.handle()
async def user_fetch(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()

    if RE_NUMBER.match(args):
        uid = int(args)

        bot.send_private_msg(user_id=event.user_id, message=f"开始获取 {uid} 用户信息")

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
