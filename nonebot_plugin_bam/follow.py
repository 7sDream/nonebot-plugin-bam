from nonebot.adapters.cqhttp import Bot, Event
from nonebot.permission import SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP
from nonebot.log import logger
from nonebot import get_driver, on_command

from .common import G_CONF, SEP, RE_NUMBER
from .database import helper
from .bilibili.user import user_info

# ===== Follower list =====

cmd_follower_list = on_command(
    SEP.join(["bam", "follower", "list"]), permission=SUPERUSER | GROUP
)


@cmd_follower_list.handle()
async def follower_list(bot: Bot, event: Event, state: dict):
    gid = None
    if await GROUP(bot, event):
        gid = event.group_id
    else:  # private, superuser
        args = str(event.message).strip()
        if RE_NUMBER.match(args):
            gid = int(args)
        else:
            return await cmd_follower_list.finish("此命令需要一个群号参数")

    group = helper.get_group_with_following_users(gid)

    if group is None:
        return await cmd_follower_list.finish("此群不在服务列表中")

    message = ["关注用户列表:"]

    for following in group.followings:
        following = following.bilibili_user
        message.append(f"{following.uid}({following.nickname})")

    if len(message) == 1:
        message.append("空")

    await cmd_follower_list.finish("\n".join(message))


# Common command check and info for follower commands


class CommandInfo:
    def __init__(self, cmd, bot, event):
        self.cmd = cmd
        self.bot = bot
        self.event = event
        self.gid = self.uid = None

    async def check(self):
        self.is_su = await SUPERUSER(self.bot, self.event)
        self.in_group = await GROUP(self.bot, self.event)
        self.message_type = "group" if self.in_group else "private"
        self.sender_id = self.event.user_id

        args = str(self.event.message).strip()

        if self.in_group:
            self.gid = self.event.group_id
            if RE_NUMBER.match(args):
                self.uid = int(args)
            else:
                await self.cmd.finish("用户 UID 无效")
                return False
        elif self.is_su:  # private, su
            parts = args.split(" ")
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

cmd_follower_add = on_command(
    SEP.join(["bam", "follower", "add"]), permission=SUPERUSER | GROUP
)


@cmd_follower_add.handle()
async def follower_add(bot: Bot, event: Event, state: dict):

    command = CommandInfo(cmd_follower_add, bot, event)

    if not await command.check():
        return

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


cmd_follower_remove = on_command(
    SEP.join(["bam", "follower", "remove"]), permission=SUPERUSER | GROUP
)


@cmd_follower_remove.handle()
async def follower_remove(bot: Bot, event: Event, state: dict):
    command = CommandInfo(cmd_follower_remove, bot, event)

    if not await command.check():
        return

    for following in command.group.followings:
        following = following.bilibili_user
        if following.uid == command.uid:
            helper.remove_link(command.gid, command.uid)
            await cmd_follower_remove.finish(
                f"成功将用户 {following.uid}({following.nickname}) 从关注列表移除"
            )
            return

    await cmd_follower_remove.finish(f"用户 {command.uid} 不在关注列表中")
