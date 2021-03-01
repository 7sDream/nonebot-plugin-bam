import importlib.resources

from nonebot.log import logger

from peewee import Model, SqliteDatabase, PeeweeException

from ..common import CONF, DRIVER

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
    from .tables import Group, BilibiliUser, BilibiliUserStatus, FollowLink
    from . import helper

    try:
        DB.create_tables([Group, BilibiliUser, BilibiliUserStatus, FollowLink])
        if CONF.bam_on_startup_clean_live_status:
            # at startup, treat everyone as having not started live streaming
            helper.clean_users_live_status()
    except PeeweeException as e:
        logger.error(f"init database failed")
        logger.error(str(e))
        raise e


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


DRIVER.on_startup(connect_database)
