import random

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (GROUP, PRIVATE, Bot,
                                         GroupMessageEvent, Message,
                                         MessageEvent)
from nonebot.log import logger
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .common import RE_NUMBER
from .database import helper

# ===== Group list =====

cmd_group_list = on_command(("bam", "group", "list"), permission=SUPERUSER)


@cmd_group_list.handle()
async def group_list(bot: Bot, event: MessageEvent):
    if not await PRIVATE(bot, event):
        await cmd_group_list.finish("只能在私聊中使用此命令")

    message = ["当前正为以下群提供服务:"]
    message.extend(
        f"{group.gid}, 管理员: {group.super_user}" for group in helper.get_all_groups()
    )
    if len(message) == 1:
        message.append("空")
    await cmd_group_list.finish("\n".join(message))


# ===== Group add =====

cmd_group_add = on_command(("bam", "group", "add"), permission=SUPERUSER)


@cmd_group_add.handle()
async def group_add(bot: Bot, event: MessageEvent):
    if not await GROUP(bot, event):
        return await cmd_group_add.finish("只能在群聊中使用此命令")

    assert(isinstance(event, GroupMessageEvent))

    gid = event.group_id

    group = helper.get_group(gid)

    if group is not None:
        await cmd_group_add.finish("此群已在服务列表中")

    group_suid = None

    args = str(event.message).strip()
    if RE_NUMBER.match(args):
        group_suid = int(args)
    else:
        group_suid = event.user_id

    helper.add_group(gid, group_suid)

    await cmd_group_add.finish(f"群 {gid}（管理员 {group_suid}）成功加入服务列表")


# ===== Group remove =====

cmd_group_remove = on_command(("bam", "group", "remove"), permission=SUPERUSER)


@cmd_group_remove.handle()
async def group_remove(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    if not await GROUP(bot, event):
        await cmd_group_remove.finish("只能在群聊中使用此命令")

    args_text = args.extract_plain_text()
    if args_text == "confirm":
        state["code"] = state["input_code"] = 0
    else:
        code = random.randint(10000000, 99999999)
        state["code"] = code
        await cmd_group_remove.pause(f"请回复以下随机码来确认删除操作: {code}")

@cmd_group_remove.got("input_code")
async def group_remove_confirm(event: GroupMessageEvent, state: T_State, input_code_arg: str = ArgPlainText()):
    code = state["code"]

    logger.debug(f"code: {code}, input: {input_code_arg}")

    input_code = 0
    if RE_NUMBER.match(input_code_arg):
        input_code = int(input_code_arg)

    if input_code != code:
        await cmd_group_remove.finish("随机码不匹配，操作取消")

    group = helper.get_group(event.group_id)

    if group is None:
        await cmd_group_remove.finish("此群不在服务列表中，无操作")
    else:
        helper.remove_group(group)
        await cmd_group_remove.finish("从服务列表移除此群成功")
