import pytest


@pytest.mark.asyncio
async def test_wbi():
    from nonebot_plugin_bam.bilibili.api import init_client
    from nonebot_plugin_bam.bilibili.live2 import room_info
    from nonebot_plugin_bam.bilibili.wbi import wbi_token

    await init_client()

    token = await wbi_token()
    assert token.ok
    
    room = await room_info(uid=774619)
    assert room.ok
    assert room.rid == 665092
