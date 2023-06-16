import nonebot
from nonebot.log import logger
from pydantic import BaseSettings


class Config(BaseSettings):
    bam_db_file: str = ":memory:"
    bam_on_startup_clean_live_status: bool = False
    bam_monitor_task_interval: int = 5
    bam_live_api: int = 2
    bam_activity_content_max_length: int = 0

    class Config:
        extra = "ignore"

CONF = Config(**nonebot.get_driver().config.dict())

def log_config():
    logger.info("[Config] configure content: " + CONF.json())

nonebot.get_driver().on_startup(log_config)
