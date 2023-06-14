import pytest


@pytest.fixture
def export():
    import nonebot
    from nonebot.adapters.console import Adapter as ConsoleAdapter

    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter("console", ConsoleAdapter)
    nonebot.load_builtin_plugins()
    nonebot.load_plugin("nonebot_plugin_bam")

    return nonebot.require("nonebot_plugin_bam")
