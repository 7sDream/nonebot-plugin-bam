import nonebot
from pydantic import BaseSettings


class Config(BaseSettings):
    bam_db_file: str = ":memory:"
    bam_on_startup_clean_live_status: bool = False
    bam_monitor_task_interval: int = 5

    class Config:
        extra = "ignore"
