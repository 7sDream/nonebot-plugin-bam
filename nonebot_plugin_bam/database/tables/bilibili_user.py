from peewee import BigIntegerField, TextField

from ..db import BaseModel


class BilibiliUser(BaseModel):
    uid = BigIntegerField(primary_key=True)
    nickname = TextField(index=True, unique=True)
    rid = BigIntegerField(index=True)  # rid = 0 means no room, so can't unique

    class Meta:
        table_name = "bilibili_users"
