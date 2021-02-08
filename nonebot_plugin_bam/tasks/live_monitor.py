import json
import asyncio
import traceback

from nonebot import require
from nonebot.log import logger
from nonebot.adapters.cqhttp import Bot

from ..database import helper
from ..common import CONF, get_bot, send_exception_to_su

scheduler = require("nonebot_plugin_apscheduler").scheduler

JOB_ID = "live_monitor"
LOGNAME = "BTASK:LIVE"
INTERVAL = CONF.bam_monitor_task_interval

if CONF.bam_live_api == 1:
    from ..bilibili.live1 import room_info, RoomInfo
elif CONF.bam_live_api == 2:
    from ..bilibili.live2 import room_info, RoomInfo
else:
    logger.error("Invalid `BAM_LIVE_API` configure value")
    exit()


@scheduler.scheduled_job(
    "interval",
    seconds=0,
    id=JOB_ID,
    max_instances=1,
    coalesce=True,
)
async def task_check_all_live_status():
    scheduler.pause_job(JOB_ID)
    try:
        await check_all_live_status()
    except Exception as e:
        logger.warning(f"[{LOGNAME}] {type(e).__name__}: {repr(e)}")
        logger.warning(f"[{LOGNAME}] {traceback.format_exc()}")
        send_exception_to_su(e)
    scheduler.resume_job(JOB_ID)


async def process_user_room_info(user, room: RoomInfo):
    ret = 0

    if room is None:
        return ret

    if room.ok:
        message = []
        if user.status.live_status == False and room.isLive == True:
            logger.info(f"[{LOGNAME}] {user.nickname} is live")
            message.extend(
                [
                    f"叮铃铃铃！{user.nickname} 开播啦！",
                    f"标题：{room.title}",
                    f"链接：{room.url}",
                ]
            )
            if room.cover:
                message.append(f"[CQ:image,file={room.cover},timeout=3]")
            ret = 1

        if user.status.live_status == True and room.isLive == False:
            logger.info(f"[{LOGNAME}] {user.nickname} is offline")
            message.extend([f"{user.nickname} 下播啦！", "期待着TA的下一次直播吧~"])
            ret = -1

        bot = get_bot()
        if bot is not None and len(message) > 0:
            group_message = "\n".join(message)
            for link in user.groups:
                group_id = link.group_id
                at_users = link.at_users
                the_group_message = group_message
                if at_users:
                    the_group_message += "\n"
                    for at_user in at_users.split(";"):
                        the_group_message += f"[CQ:at,qq={at_user}]"
                try:
                    await bot.send_group_msg(
                        group_id=group_id,
                        message=the_group_message,
                        auto_escape=False,
                    )
                except Exception as e:
                    send_exception_to_su(e, "\n".join(the_group_message))
    elif hasattr(room, "code"):
        logger.warning(
            f"[{LOGNAME}] check {user.nickname}({user.uid})'s room failed: {room.code} {room.message}"
        )
    return ret


async def check_all_live_status():
    logger.info(f"[{LOGNAME}] Start check live status")

    users = helper.get_users_with_linked_groups_and_status()

    live_become_open_users = []
    live_become_closed_users = []

    for user in filter(lambda u: len(u.groups) > 0, users.values()):
        room = None
        try:
            logger.info(f"[{LOGNAME}] checking {user.nickname} live status...")
            room = await room_info(uid=user.uid, rid=user.rid)
            if not room.ok and hasattr(room, "code"):
                logger.warning(
                    f"[{LOGNAME}] check {user.nickname}({user.uid})'s room failed: {room.code} {room.message}"
                )
        except Exception as e:
            logger.warning(
                f"[{LOGNAME}] check {user.uid} live status task failed: {str(e)}"
            )

        ret = await process_user_room_info(user, room)

        if ret > 0:
            live_become_open_users.append(user)
        if ret < 0:
            live_become_closed_users.append(user)

        await asyncio.sleep(INTERVAL)

    helper.set_user_live_status_in(live_become_open_users)
    helper.clean_user_live_status_in(live_become_closed_users)
