from .activity import cmd_bilibili_activity_info
from .bilibili.api import init_client
from .config import Config
from .follow import cmd_follower_add, cmd_follower_list, cmd_follower_remove
from .group import cmd_group_add, cmd_group_list, cmd_group_remove
from .tasks.activity_monitor import task_check_new_activity
from .tasks.live_monitor import task_check_all_live_status
from .user import cmd_user_fetch

__version__ = "0.2.0"

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name = "BAM",
    description="Bilibili Activity Monitor",
    usage="Bilibili用户动态/开播监控器",
    config = Config,
    extra={},
)
