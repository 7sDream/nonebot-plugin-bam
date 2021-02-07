from peewee import TextField, ForeignKeyField, CompositeKey

from .group import Group
from .bilibili_user import BilibiliUser
from ..db import BaseModel


class FollowLink(BaseModel):
    group = ForeignKeyField(Group, on_delete="CASCADE", backref="followings")
    bilibili_user = ForeignKeyField(BilibiliUser, backref="groups")
    at_users = TextField()

    class Meta:
        table_name = "follow_links"
        primary_key = CompositeKey("group", "bilibili_user")
