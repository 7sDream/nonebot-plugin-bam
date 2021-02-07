from .api import APIResult


class UserInfo(APIResult):
    URL = "https://api.bilibili.com/x/space/acc/info?mid={uid}"

    def __init__(self):
        super().__init__()

    def __initialize__(self, body, *, uid):
        self.uid = uid
        self.ok = body["code"] == 0

        if self.ok:
            data = body["data"]
            self.nickname = data["name"]
            self.rid = data["live_room"]["roomid"]


async def user_info(uid) -> UserInfo:
    info = await UserInfo.of(uid=uid)
    return info
