from nonebot import on_command
from nonebot.adapters.onebot.v11 import (Bot, GroupMessageEvent, Message,
                                         MessageEvent)
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .bilibili.user import user_info
from .common import RE_NUMBER
from .database import helper

# ===== Follower list =====

cmd_follower_list = on_command(
    ("bam", "follower", "list"), permission=SUPERUSER | GROUP
)


@cmd_follower_list.handle()
async def follower_list(event: MessageEvent, args: Message = CommandArg()):
    gid = None
    if isinstance(event, GroupMessageEvent):
        gid = event.group_id
    else:  # private, superuser
        args_text = args.extract_plain_text().strip()
        if RE_NUMBER.match(args_text):
            gid = int(args_text)
        else:
            await cmd_follower_list.finish("此命令需要一个群号参数")

    group = helper.get_group_with_following_users(gid)

    if group is None:
        await cmd_follower_list.finish("此群不在服务列表中")

    message = ["关注用户列表:"]

    for following in group.followings: # type: ignore
        following = following.bilibili_user
        message.append(f"{following.uid}({following.nickname})")

    if len(message) == 1:
        message.append("空")

    await cmd_follower_list.finish("\n".join(message))


# Common command check and info for follower commands


class CommandInfo:
    def __init__(self, cmd, bot: Bot, event: MessageEvent, args: Message):
        self.cmd = cmd
        self.bot = bot
        self.event = event
        self.args = args.extract_plain_text().strip()
        self.gid = self.uid = None

    async def check(self):
        self.is_su = await SUPERUSER(self.bot, self.event)
        self.in_group = await GROUP(self.bot, self.event)
        self.message_type = "group" if self.in_group else "private"
        self.sender_id = self.event.user_id

        if self.in_group:
            assert isinstance(self.event, GroupMessageEvent)
            self.gid = self.event.group_id
            if RE_NUMBER.match(self.args):
                self.uid = int(self.args)
            else:
                await self.cmd.finish("用户 UID 无效")
                return False
        elif self.is_su:  # private, su
            parts = self.args.split(" ")
            if len(parts) != 2:
                return await self.cmd.finish("缺少参数，需要群号和 UID")
            if RE_NUMBER.match(parts[0]):
                self.gid = int(parts[0])
            else:
                await self.cmd.finish("群号无效")
                return False
            if RE_NUMBER.match(parts[1]):
                self.uid = int(parts[1])
            else:
                await self.cmd.finish("UID 无效")
                return False

        self.group = helper.get_group_with_following_users(self.gid)
        if self.group is None:
            await self.cmd.finish("此群不在服务列表中")
            return False

        if not self.is_su and self.group.super_user != self.sender_id:
            await self.cmd.finish("你没有使用此命令的权限")
            return False

        return True

    async def send(self, message):
        await self.bot.send_msg(
            message_type=self.message_type,
            group_id=self.gid,
            user_id=self.sender_id,
            message=message,
        )


# ===== Follower add =====

cmd_follower_add = on_command(("bam", "follower", "add"), permission=SUPERUSER | GROUP)


@cmd_follower_add.handle()
async def follower_add(bot: Bot, event: MessageEvent, args: Message = CommandArg()):

    command = CommandInfo(cmd_follower_add, bot, event, args)

    if not await command.check():
        return

    assert(command.group is not None)

    for following in command.group.followings:
        following = following.bilibili_user
        if following.uid == command.uid:
            return await cmd_follower_add.finish(f"用户 {command.uid} 已在关注列表内")

    user = helper.get_user(command.uid)

    if user is None:
        await command.send(f"获取 {command.uid} 用户信息中，请稍候……")
        user = await user_info(uid=command.uid)

        if user.ok:
            user = helper.add_user(user.uid, user.nickname, user.rid)
        else:
            return await cmd_follower_add.finish(f"获取 {command.uid} 用户信息失败")

    await command.send(f"UID: {user.uid}, 昵称: {user.nickname}, 直播间: {user.rid}")

    helper.add_link(command.group, user)
    return await cmd_follower_add.finish(f"成功加入关注列表")

# ===== Follower remove =====

cmd_follower_remove = on_command(
    ("bam", "follower", "remove"), permission=SUPERUSER | GROUP
)


@cmd_follower_remove.handle()
async def follower_remove(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    command = CommandInfo(cmd_follower_remove, bot, event, args)

    if not await command.check():
        return

    assert(command.group is not None)

    for following in command.group.followings:
        following = following.bilibili_user
        if following.uid == command.uid:
            helper.remove_link(command.gid, command.uid)
            await cmd_follower_remove.finish(
                f"成功将用户 {following.uid}({following.nickname}) 从关注列表移除"
            )

    await cmd_follower_remove.finish(f"用户 {command.uid} 不在关注列表中")
