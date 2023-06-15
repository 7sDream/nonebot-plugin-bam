import datetime
from typing import Dict, Generator, List, Optional, TypedDict

from nonebot.log import logger
from peewee import JOIN

from .db import DB
from .tables import BilibiliUser, BilibiliUserStatus, FollowLink, Group


def log_sql(s):
    logger.debug(f"[DB:SQL] {s.sql()}")
    return s


def get_all_groups() -> Generator[Group, None, None]:
    yield from log_sql(Group.select())


def get_group(gid: int) -> Optional[Group]:
    for group in log_sql(Group.select().where(Group.gid == gid)):
        return group
    return None


def add_group(gid: int, group_suid: int) -> None:
    return log_sql(
        Group.insert(gid=gid, super_user=group_suid).on_conflict_replace()
    ).execute()


def remove_group(group: Group) -> None:
    group.delete_instance(recursive=True, delete_nullable=True)

class BilibiliUserWithGroupAndStatus(BilibiliUser):
    groups: List[FollowLink]
    status: BilibiliUserStatus

def get_users_with_linked_groups_and_status() -> Dict[int, BilibiliUserWithGroupAndStatus]:
    users = {}
    for user in log_sql(
        BilibiliUser.select(BilibiliUser, FollowLink, BilibiliUserStatus)
        .join(FollowLink, JOIN.LEFT_OUTER)
        .switch(BilibiliUser)
        .join(BilibiliUserStatus, JOIN.LEFT_OUTER, attr="status")
    ):
        users[user.uid] = user

    return users


def clean_users_live_status() -> None:
    log_sql(BilibiliUserStatus.update(live_status=False)).execute(None)


def clean_user_live_status_in(users) -> None:
    if len(users) > 0:
        log_sql(
            BilibiliUserStatus.update(live_status=False).where(
                BilibiliUserStatus.bilibili_user.in_(users)
            )
        ).execute()


def set_user_live_status_in(users) -> None:
    if len(users) > 0:
        log_sql(
            BilibiliUserStatus.update(live_status=True).where(
                BilibiliUserStatus.bilibili_user.in_(users)
            )
        ).execute()

class GroupWithFollowingUsers:
    gid: int
    super_user: int
    created_date: datetime.datetime
    followings: List[FollowLink]

def get_group_with_following_users(gid) -> Optional[GroupWithFollowingUsers]:
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


def add_user(uid, nickname, rid) -> BilibiliUser:
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


def add_link(group, user) -> None:
    FollowLink.create(group=group, bilibili_user=user)


def remove_link(gid, uid) -> None:
    log_sql(
        FollowLink.delete().where(
            (FollowLink.group == gid) & (FollowLink.bilibili_user == uid)
        )
    ).execute()


def update_user_newest_activity_id(data: dict[int, int]) -> None:
    with DB.atomic():
        for user, act_id in data.items():
            BilibiliUserStatus.update(newest_activity_id=act_id).where(
                BilibiliUserStatus.bilibili_user == user
            ).execute()
