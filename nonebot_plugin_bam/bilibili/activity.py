import json

from nonebot.log import logger

from ..common import CONF, cq_encode
from .api import APIResult

MAX_LENGTH = CONF.bam_activity_content_max_length


def shorten(s):
    if MAX_LENGTH > 0 and len(s) > MAX_LENGTH:
        return s[0:MAX_LENGTH] + "...(内容过长省略)"
    return s


class Activity:
    KNOWN_TYPES_MAP: dict = {}

    @staticmethod
    def isInvalid(card):
        try:
            if card["desc"]["status"] == 0:
                return True
        except KeyError:
            pass
        try:
            if card["card"]["item"]["miss"] == 1:
                return True
        except (KeyError, TypeError):
            pass

        return False

    def __new__(cls, card):
        if cls.isInvalid(card):
            return super().__new__(InvalidActivity)
        t = card["desc"]["type"]
        instance = super().__new__(cls.get_subclass_by_type(t))
        return instance

    @classmethod
    def get_subclass_by_type(cls, t):
        if not cls.KNOWN_TYPES_MAP:
            cls.KNOWN_TYPES_MAP = cls.build_known_types_map()
        if t in cls.KNOWN_TYPES_MAP:
            return cls.KNOWN_TYPES_MAP[t]
        else:
            return UnTestedActivity

    @classmethod
    def build_known_types_map(cls):
        return {
            sub.TYPE_VALUE: sub
            for sub in cls.__subclasses__()
            if getattr(sub, "TYPE_VALUE", None) is not None
        }

    def __init__(self, card):
        self._desc_data = card["desc"]
        if isinstance(card["card"], str):
            self._card_data = json.loads(card["card"])
        else:
            self._card_data = card["card"]
        self.id = self._desc_data["dynamic_id"]
        self.uid = self._desc_data["uid"]
        if "user" in self._card_data:
            if "uname" in self._card_data["user"]:
                self.username = self._card_data["user"]["uname"]
            if "name" in self._card_data["user"]:
                self.username = self._card_data["user"]["name"]

    def display(self):
        pass

    def url(self):
        return f"https://t.bilibili.com/{self.id}"


class InvalidActivity(Activity):
    def __init__(self, card):
        super().__init__(card)
        self.content = self._card_data["item"]["tips"]

    def display(self):
        return self.content


class RepostActivity(Activity):
    TYPE_VALUE = 1

    def __init__(self, card):
        super().__init__(card)
        self.content = self._card_data["item"]["content"]
        data = {
            "desc": card["desc"]["origin"],
            "card": self._card_data["origin"]
            if "origin" in self._card_data
            else self._card_data,
        }
        self.origin = Activity(data)

    def display(self) -> str:
        if isinstance(self.origin, InvalidActivity):
            origin_user = "未知用户"
        else:
            origin_user = getattr(
                self.origin, "username", f"ID 为 {self.origin.uid} 的用户"
            )
        return "\n".join(
            [
                f"转发了 {origin_user} 的动态，并说：",
                "",
                f"{shorten(self.content)}",
                "",
                f"动态链接：{self.url()}",
                "==========",
                f"{origin_user} 的原动态内容：",
                "",
                self.origin.display(),
            ]
        )


class PictureActivity(Activity):
    TYPE_VALUE = 2

    def __init__(self, card):
        super().__init__(card)
        self.content = self._card_data["item"]["description"]
        self.pics = [pic["img_src"] for pic in self._card_data["item"]["pictures"]]

    def display(self):
        messages = [
            f"{shorten(self.content)}",
            "",
            f"附带 {len(self.pics)} 张图片：",
        ]
        messages.extend(
            [f"[CQ:image,file={pic},timeout=10]" for _, pic in zip(range(2), self.pics)]
        )
        if len(self.pics) > 2:
            messages.append(f"避免消息过长，余下 {len(self.pics) - 2} 张图片不转发，请点击链接查看")
        messages.append("")
        messages.append(f"动态链接：{self.url()}")
        return "\n".join(messages)


class TextActivity(Activity):
    TYPE_VALUE = 4

    def __init__(self, card):
        super().__init__(card)
        self.content = self._card_data["item"]["content"]

    def display(self):
        return "\n".join([f"{shorten(self.content)}", "", f"动态链接：{self.url()}"])


class VideoActivity(Activity):
    TYPE_VALUE = 8

    def __init__(self, card):
        super().__init__(card)
        self.uid = self._card_data["owner"]["mid"]
        self.username = self._card_data["owner"]["name"]
        self.av = self._card_data["aid"]
        self.title = self._card_data["title"]
        self.desc = self._card_data["desc"]
        self.content = self._card_data["dynamic"]
        self.video_url = f"https://bilibili.com/av{self.av}"

    def display(self):
        messages = [
            f"投稿了视频：{self.title}",
            "",
            f"简介：",
            shorten(self.desc),
            "",
        ]

        if self.content and self.content != self.desc:
            messages.extend([f"动态内容：{shorten(self.content)}", ""])

        messages.extend([f"视频链接：{self.video_url}", f"动态链接：{self.url()}"])

        return "\n".join(messages)


class ArticleActivity(Activity):
    TYPE_VALUE = 64

    def __init__(self, card):
        super().__init__(card)
        self.uid = self._card_data["author"]["mid"]
        self.username = self._card_data["author"]["name"]
        self.aid = self._card_data["id"]
        self.title = self._card_data["title"]
        self.summary = self._card_data["summary"]
        self.cover = self._card_data["banner_url"]
        self.article_url = f"https://www.bilibili.com/read/cv{self.aid}"

    def display(self):
        messages = [
            f"投稿了新文章：{self.title}",
        ]
        if self.cover:
            messages.append(f"[CQ:image,file={self.cover},timeout=3]")
        messages.extend(
            [
                "",
                f"摘要：{shorten(self.summary)}",
                "",
                f"文章链接：{self.article_url}",
                f"动态链接：{self.url()}",
            ]
        )
        return "\n".join(messages)


class LiveRoomActivity(Activity):
    TYPE_VALUE = 4200

    def __init__(self, card):
        super().__init__(card)
        self.uid = self._card_data["uid"]
        self.username = self._card_data["uname"]
        self.rid = self._card_data["roomid"]
        self.live_url = f"https://live.bilibili.com/{self.rid}"
        self.title = self._card_data["title"]
        self.cover = self._card_data["cover"]
        self.area_parent = self._card_data["area_v2_parent_name"]
        self.area = self._card_data["area_v2_name"]

    def display(self):
        return "\n".join(
            [
                f"{self.username} 在 {self.area_parent}/{self.area} 分区的直播间",
                f"标题：{self.title}",
                f"[CQ:image,file={self.cover},timeout=3]",
                f"直播间：{self.live_url}",
                f"动态链接：{self.url()}",
            ]
        )


class H5Activity(Activity):
    TYPE_VALUE = 2048

    def __init__(self, card):
        super().__init__(card)
        self.uid = self._card_data["user"]["uid"]
        self.username = self._card_data["user"]["uname"]
        self.content = self._card_data["vest"]["content"]
        self.h5_title = self._card_data["sketch"]["title"]
        self.h5_desc = self._card_data["sketch"]["desc_text"]
        self.h5_url = self._card_data["sketch"]["target_url"]
        self.h5_cover = self._card_data["sketch"]["cover_url"]

    def display(self):
        return "\n".join(
            [
                f"{shorten(self.content)}",
                "",
                f"附带一个 H5 页面：{self.h5_title} - {self.h5_desc}",
                "",
                f"动态链接：{self.url()}",
            ]
        )

    def h5_share_card(self):
        return f"[CQ:share,url={cq_encode(self.h5_url)},title={cq_encode(self.h5_title)},image={cq_encode(self.h5_cover)}]"


class UnTestedActivity(Activity):
    TYPES = {
        1: "转发",
        2: "带图动态",
        4: "纯文字动态",
        8: "视频",
        16: "小视频(未实现)",
        32: "DRAMA(未实现)",
        64: "文章",
        256: "音乐(未实现)",
        512: "番剧(未实现)",
        1000: "热门(未实现)",
        1001: "Quick(未实现)",
        1024: "空(未实现)",
        2048: "H5页面(未实现)",
        2049: "漫画(未实现)",
        4097: "PGC番剧(未实现)",
        4098: "电影(未实现)",
        4099: "电视剧(未实现)",
        4100: "国创(未实现)",
        4101: "纪录片(未实现)",
        4200: "直播间",
        4201: "直播(未实现)",
        4300: "播放列表(未实现)",
        4302: "Cheese 系列(未实现)",
        4303: "Cheese 更新(未实现)",
        4308: "直播推送(未实现)",
    }

    def __init__(self, card):
        super().__init__(card)
        self.type_value = card["desc"]["type"]

    def display(self):
        type_desc = str(self.type_value)
        if self.type_value in self.TYPES:
            type_desc = self.TYPES[self.type_value]
        return "\n".join([f"尚未支持的动态类型：{type_desc}", "", f"动态链接：{self.url()}"])


class ActivityList(APIResult):
    URL = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=0&host_uid={uid}&offset_dynamic_id={offset}&need_top=0&platform=web&ts={ts}"

    def __init__(self):
        super().__init__()

    def __initialize__(self, body, *, uid, offset):
        self.uid = uid
        self.ok = body["code"] == 0
        self.__data = []
        if self.ok and "cards" in body["data"]:
            for card in body["data"]["cards"]:
                act = None
                try:
                    act = Activity(card)
                except Exception as e:
                    logger.warning(
                        f"[BAM:BILIBILI:API:ActivityList] of {self.uid}: {type(e).__name__} {repr(e)}: {card}"
                    )
                self.__data.append(act)

    def __len__(self):
        if self.ok:
            return len(self.__data)
        else:
            return 0

    def __getitem__(self, key):
        return self.__data[key]

    def __iter__(self):
        return iter(self.__data)


async def activity_list(uid, offset=None):
    if offset is None:
        offset = 0
    return await ActivityList.of(uid=uid, offset=offset)


class OneActivity(APIResult):
    URL = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={act_id}&ts={ts}"

    def __init__(self):
        super().__init__()

    def __initialize__(self, data, *, act_id):
        self.ok = data["code"] == 0
        if self.ok:
            try:
                self.act = Activity(data["data"]["card"])
            except Exception as e:
                logger.warning(
                    f"[BAM:BILI:API:OneActivity] {type(e).__name__} {repr(e)}: {data}"
                )
                self.ok = False


async def activity(act_id):
    act = await OneActivity.of(act_id=act_id)
    if act.ok:
        return act.act
    return None
