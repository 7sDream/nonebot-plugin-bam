import datetime

from peewee import BigIntegerField, DateTimeField

from ..db import BaseModel


class Group(BaseModel):
    gid = BigIntegerField(primary_key=True)
    super_user = BigIntegerField()
    created_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "groups"
