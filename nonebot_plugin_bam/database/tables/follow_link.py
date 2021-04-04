from peewee import CompositeKey, ForeignKeyField, TextField

from ..db import BaseModel
from .bilibili_user import BilibiliUser
from .group import Group


class FollowLink(BaseModel):
    group = ForeignKeyField(Group, on_delete="CASCADE", backref="followings")
    bilibili_user = ForeignKeyField(BilibiliUser, backref="groups")
    at_users = TextField(default="")

    class Meta:
        table_name = "follow_links"
        primary_key = CompositeKey("group", "bilibili_user")
