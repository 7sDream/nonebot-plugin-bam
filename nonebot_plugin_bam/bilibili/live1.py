from .api import APIResult


class RoomInfo(APIResult):
    URL = "https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld?mid={uid}&ts={ts}"

    def __init__(self):
        super().__init__()

    def __initialize__(self, body, *, uid):
        self.uid = uid
        self.code = body["code"]
        self.message = body["message"]
        self.ok = body["code"] == 0 and body["data"]["roomid"] != 0
        if self.ok:
            data = body["data"]
            self.rid = data["roomid"]
            self.isLive = data["liveStatus"] == 1
            self.title = data["title"]
            self.cover = data["cover"]
            self.url = data["url"]

async def room_info(uid=None, rid=None) -> RoomInfo:
    room = await RoomInfo.of(uid=uid)
    return room
