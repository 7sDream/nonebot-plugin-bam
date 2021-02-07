from peewee import BigIntegerField, BooleanField, ForeignKeyField

from ..db import BaseModel
from .bilibili_user import BilibiliUser


class BilibiliUserStatus(BaseModel):
    bilibili_user = ForeignKeyField(
        BilibiliUser,
        primary_key=True,
        backref="statuses",
        on_delete="CASCADE",
    )
    newest_activity_id = BigIntegerField()
    live_status = BooleanField(index=True)

    class Meta:
        table_name = "bilibili_user_status"
