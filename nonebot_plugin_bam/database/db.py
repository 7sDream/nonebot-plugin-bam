from nonebot import get_driver
from nonebot.log import logger
from peewee import Model, PeeweeException, SqliteDatabase

from ..config import CONF

LOGNAME = "DATABASE"

DB = SqliteDatabase(
    CONF.bam_db_file,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "ignore_check_constraints": 0,
    },
)


class BaseModel(Model):
    class Meta:
        database = DB


def init_database():
    from . import helper
    from .tables import BilibiliUser, BilibiliUserStatus, FollowLink, Group

    try:
        DB.create_tables([Group, BilibiliUser, BilibiliUserStatus, FollowLink])
        if CONF.bam_on_startup_clean_live_status:
            # at startup, treat everyone as having not started live streaming
            helper.clean_users_live_status()
    except PeeweeException as e:
        logger.error(f"init database failed")
        logger.error(str(e))
        raise e

    logger.success(f"[{LOGNAME}] init ok")

def connect_database():
    if CONF.bam_db_file == ":memory:":
        logger.warning("use memory db will lost all data after restart")
        logger.warning("set db location to a file path is highly recommended")

    try:
        DB.connect()
    except PeeweeException as e:
        logger.error(f"connect to {CONF.bam_db_file} failed")
        logger.error(str(e))
        raise e

    init_database()


get_driver().on_startup(connect_database)
