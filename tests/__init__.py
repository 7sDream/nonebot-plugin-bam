import nonebot
from nonebot.adapters.console import Adapter as ConsoleAdapter

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(ConsoleAdapter)
nonebot.load_builtin_plugins()
nonebot.load_plugin("nonebot_plugin_bam")

