import json
import os


def load_data(name):
    with open(os.path.join("tests", "act_data", name), "rb") as f:
        j = json.load(f)
        return j["data"]["card"]

def test_h5():
    from nonebot_plugin_bam.bilibili.activity import Activity

    act = Activity(load_data("h5.json"))
    assert act.uid == 1926156228
    assert act.username == "希亚娜Ciyana"
    assert act.h5_title == "希亚娜Ciyana的直播日历"
    assert (
        act.h5_url
        == "https://live.bilibili.com/p/html/live-app-calendar/index.html?is_live_webview=1&hybrid_set_header=2&share_source=bili&share_medium=web&bbid=492831DB-BC20-408E-9ADF-872343C28FA6143081infoc&ts=1614573029062#/home/search?ruid=1926156228"
    )
    print(act.display())
    print(act.h5_share_card())
