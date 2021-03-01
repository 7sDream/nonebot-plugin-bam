import json
import asyncio
import traceback
from datetime import datetime, timedelta

from nonebot import require
from nonebot.log import logger
from nonebot.adapters.cqhttp import Bot

from ..database import helper
from ..bilibili.activity import activity_list, ActivityList, H5Activity
from ..common import CONF, get_bot, send_exception_to_su

scheduler = require("nonebot_plugin_apscheduler").scheduler

JOB_ID = "activity_monitor"
LOGNAME = "TASK:ACTIVITY"
INTERVAL = CONF.bam_monitor_task_interval


@scheduler.scheduled_job(
    "interval",
    seconds=0,
    id=JOB_ID,
    next_run_time=datetime.now() + timedelta(seconds=INTERVAL / 2.0),
    max_instances=1,
    coalesce=True,
)
async def task_check_new_activity():
    scheduler.pause_job(JOB_ID)
    try:
        await check_new_activity()
    except Exception as e:
        logger.warning(f"[{LOGNAME}] Outer Exception {type(e).__name__}: {repr(e)}")
        logger.warning(f"[{LOGNAME}] {traceback.format_exc()}")
        send_exception_to_su(e)
    scheduler.resume_job(JOB_ID)


async def process_user_actlist(user, actlist: ActivityList):
    has_new = False
    latest = 0
    if actlist is None:
        return has_new, latest

    latest = user.status.newest_activity_id
    if actlist.ok:
        latest_id = actlist[0].id if len(actlist) > 0 else "no act"
        logger.info(
            f"[{LOGNAME}] {user.nickname}({user.uid})'s last act id: {latest_id}"
        )
        if latest == 0:  # first fetch, only get latest id
            for _, act in zip(range(1), actlist):
                if act is not None:
                    latest = act.id
                    has_new = True
        else:  # get new activities
            bot = get_bot()
            for _, act in reversed(list(zip(range(3), actlist))):  # max send 3
                if act is None:
                    continue

                if act.id > latest:
                    has_new = True
                    latest = act.id
                    if bot is not None:
                        group_message = f"叮铃铃铃！{user.nickname} 有新动态！\n{act.display()}"
                        h5_share_card = None
                        if isinstance(act, H5Activity):
                            h5_share_card = act.h5_share_card()
                        for link in user.groups:
                            group_id = link.group_id
                            at_users = link.at_users
                            the_group_message = group_message
                            if at_users:
                                the_group_message += "\n"
                                for at_user in at_users.split(";"):
                                    the_group_message += f"[CQ:at,qq={at_user}]"
                            logger.info(f"Send activity message: {the_group_message}")
                            try:
                                await bot.send_group_msg(
                                    group_id=group_id,
                                    message=the_group_message,
                                    auto_escape=False,
                                )
                            except Exception as e:
                                send_exception_to_su(e, the_group_message)
                            if h5_share_card is not None:
                                try:
                                    await bot.send_group_msg(
                                        group_id=group_id,
                                        message=h5_share_card,
                                        auto_escape=False,
                                    )
                                except Exception as e:
                                    pass
    elif hasattr(actlist, "code"):
        logger.info(
            f"[{LOGNAME}] check {user.nickname}({user.uid}) failed: {actlist.code} {actlist.message}"
        )
    return has_new, latest


async def check_new_activity():
    logger.info(f"[{LOGNAME}] Start check new activities")

    users = helper.get_users_with_linked_groups_and_status()

    user_newest_activity_ids = {}

    for user in filter(lambda u: len(u.groups) > 0, users.values()):
        actlist = None
        try:
            logger.info(f"[{LOGNAME}] checking {user.nickname} activities...")
            actlist = await activity_list(uid=user.uid)
            if not actlist.ok and hasattr(actlist, "code"):
                logger.warning(
                    f"[{LOGNAME}] check {user.nickname}({user.uid})'s activities failed: {actlist.code} {actlist.message}"
                )
        except Exception as e:
            logger.warning(
                f"[{LOGNAME}] check {user.uid} activity list task failed: {str(e)}"
            )
        has_new, latest = await process_user_actlist(user, actlist)

        if has_new:
            user_newest_activity_ids[user] = latest
        await asyncio.sleep(INTERVAL)

    if user_newest_activity_ids:
        try:
            helper.update_user_newest_activity_id(user_newest_activity_ids)
        except Exception as e:
            logger.warning(
                f"[{LOGNAME}] Update db exception {type(e).__name__}: {repr(e)}"
            )
