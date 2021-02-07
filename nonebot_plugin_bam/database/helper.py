from collections import defaultdict
from typing import Dict
from peewee import JOIN

from nonebot.log import logger

from .db import DB
from .tables import Group, FollowLink, BilibiliUser, BilibiliUserStatus


def log_sql(s):
    # logger.debug(f"[DB:SQL] {s.sql()}")
    return s


def get_all_groups():
    yield from log_sql(Group.select())


def get_group(gid: int) -> Group:
    for group in log_sql(Group.select().where(Group.gid == gid)):
        return group
    return None


def add_group(gid: int, group_suid: int):
    return log_sql(
        Group.insert(gid=gid, super_user=group_suid).on_conflict_replace()
    ).execute()


def remove_group(group: Group):
    group.delete_instance(recursive=True, delete_nullable=True)


def get_users_with_linked_groups_and_status() -> Dict[int, BilibiliUser]:
    users = {}
    for user in log_sql(
        BilibiliUser.select(BilibiliUser, FollowLink, BilibiliUserStatus)
        .join(FollowLink, JOIN.LEFT_OUTER)
        .switch(BilibiliUser)
        .join(BilibiliUserStatus, JOIN.LEFT_OUTER, attr="status")
    ):
        users[user.uid] = user

    return users


def clean_users_live_status():
    log_sql(BilibiliUserStatus.update(live_status=False)).execute(None)


def clean_user_live_status_in(users):
    if len(users) > 0:
        log_sql(
            BilibiliUserStatus.update(live_status=False).where(
                BilibiliUserStatus.bilibili_user.in_(users)
            )
        ).execute()


def set_user_live_status_in(users):
    if len(users) > 0:
        log_sql(
            BilibiliUserStatus.update(live_status=True).where(
                BilibiliUserStatus.bilibili_user.in_(users)
            )
        ).execute()


def get_group_with_following_users(gid):
    for group in log_sql(
        Group.select()
        .where(Group.gid == gid)
        .join(FollowLink, JOIN.LEFT_OUTER)
        .join(BilibiliUser, JOIN.LEFT_OUTER)
    ):
        return group
    return None


def get_user(uid):
    for user in log_sql(BilibiliUser.select().where(BilibiliUser.uid == uid)):
        return user
    return None


def add_user(uid, nickname, rid):
    user, created = BilibiliUser.get_or_create(
        uid=uid, defaults={"nickname": nickname, "rid": rid}
    )
    if created:
        BilibiliUserStatus.create(
            bilibili_user=user, newest_activity_id=0, live_status=False
        )
    else:
        user.nickname = nickname
        user.rid = rid
        user.save()
    return user


def add_link(group, user):
    FollowLink.create(group=group, bilibili_user=user)


def remove_link(gid, uid):
    log_sql(
        FollowLink.delete().where(
            (FollowLink.group == gid) & (FollowLink.bilibili_user == uid)
        )
    ).execute()


def update_user_newest_activity_id(data: dict[int, int]):
    with DB.atomic():
        for user, act_id in data.items():
            BilibiliUserStatus.update(newest_activity_id=act_id).where(
                BilibiliUserStatus.bilibili_user == user
            ).execute()
