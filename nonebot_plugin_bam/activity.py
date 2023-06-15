from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, GROUP, PRIVATE
from nonebot.rule import to_me

from .bilibili.activity import H5Activity, activity
from .common import RE_NUMBER

cmd_bilibili_activity_info = on_command(
    ("bam", "act"), rule=to_me(), permission=GROUP | PRIVATE, block=True
)


@cmd_bilibili_activity_info.handle()
async def bilibili_activity_info(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    messages = []

    if await GROUP(bot, event):
        messages.append(f"[CQ:at,qq={event.user_id}]")

    arg_text = args.extract_plain_text().strip()

    if RE_NUMBER.match(arg_text) is None:
        messages.append("参数错误，请输入正确的动态 ID")
        await cmd_bilibili_activity_info.finish("\n".join(messages))

    act_id = int(arg_text)

    act = await activity(act_id)

    if act is None:
        messages.append("获取动态信息失败")
        await cmd_bilibili_activity_info.finish("\n".join(messages))

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
