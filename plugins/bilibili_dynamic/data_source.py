from datetime import datetime, timedelta, timezone as tz, UTC
from operator import itemgetter

from ATRI.message import MessageBuilder
from ATRI.utils import TimeDealer
from ATRI.exceptions import BaseBotException
from ATRI.database import DatabaseWrapper, add_database

from . import model
from .api import API
from .model import BilibiliSubscription

_OUTPUT_FORMAT = (
    MessageBuilder("{up_nickname} 的{up_dy_type}更新了!")
    .text("{up_dy_content}")
    .text("链接: {up_dy_link}")
    .done()
)
add_database("bilibili", model)
DB = DatabaseWrapper(BilibiliSubscription)


class BilibiliDynamicError(BaseBotException):
    prompt = "b站动态订阅错误"


class BilibiliDynamicSubscriptor:
    async def __add_sub(self, uid: int, group_id: int):
        try:
            await DB.add_sub(uid=uid, group_id=group_id)
        except Exception:
            raise BilibiliDynamicError("添加订阅失败")

    async def update_sub(self, uid: int, group_id: int, update_map: dict):
        try:
            await DB.update_sub(update_map=update_map, uid=uid, group_id=group_id)
        except Exception:
            raise BilibiliDynamicError("更新订阅失败")

    async def __del_sub(self, uid: int, group_id: int):
        try:
            await DB.del_sub({"uid": uid, "group_id": group_id})
        except Exception:
            raise BilibiliDynamicError("删除订阅失败")

    async def get_sub_list(self, uid: int = int(), group_id: int = int()) -> list:
        if not uid:
            query_map = {"group_id": group_id}
        else:
            query_map = {"uid": uid, "group_id": group_id}

        try:
            return await DB.get_sub_list(query_map)
        except Exception:
            raise BilibiliDynamicError("获取订阅列表失败")

    async def get_all_subs(self) -> list:
        try:
            return await DB.get_all_subs()
        except Exception:
            raise BilibiliDynamicError("获取全部订阅列表失败")

    async def __get_up_nickname(self, uid: int) -> str | None:
        api = API(uid)
        resp = await api.get_user_info()
        data = resp.get("data", dict())
        return data.get('card', {}).get("name", None)

    async def get_up_recent_dynamic(self, uid: int) -> dict:
        api = API(uid)
        resp = await api.get_user_dynamics()
        data = resp.get("data", {})
        return data

    def extract_dyanmic(self, data: list) -> list:
        result = list()
        for i in data:
            pattern = {}
            models = i["modules"]
            major = models['module_dynamic']["major"]
            comment_type = i["basic"]["comment_type"]
            author = models['module_author']

            # common 部分
            pattern["type"] = i['type']
            pattern["uid"] = author["mid"]
            pattern["timestamp"] = author['pub_ts']
            pattern["time"] = TimeDealer(
                float(pattern["timestamp"]), tz(timedelta(hours=8))
            ).to_datetime()
            pattern["type_zh"] = str()

            # alternative 部分
            pattern["content"] = str()
            pattern["pic"] = []

            # 根据type区分 提取content
            if comment_type == 1:  # 视频动态
                pattern["type_zh"] = "视频动态"
                archive = major["archive"]
                pattern["content"] = "视频标题: " + archive['title'] + '\n' + archive['desc']
                pattern["jump_url"] = 'https:' + archive['jump_url']
                pattern["pic"] = [archive.get('cover', None)]
            elif comment_type == 11:  # 普通动态
                pattern["type_zh"] = "普通动态"
                opus = major["opus"]
                pattern["content"] = opus['summary']['text']
                pattern["jump_url"] = 'https:' + opus['jump_url']
                pattern['pic'] = opus['pics']
            elif comment_type == 17:
                pattern["type_zh"] = "转发动态"
                opus = i['orig']["modules"]['module_dynamic']["major"]["opus"]
                pattern['content'] = models['module_dynamic']['desc']['text'] + '\n转发的原文链接:https:' + opus[
                    'jump_url']
                pattern["jump_url"] = 'https://t.bilibili.com/' + i['id_str']
            else:
                pattern["type_zh"] = "未知类型动态"
                pattern["content"] = "未知类型动态，请等待更新"
                pattern["jump_url"] = 'https://t.bilibili.com/' + i.get('id_str', '')

            result.append(pattern)
        return sorted(result, key=itemgetter("timestamp"))

    def gen_output(self, data: dict, content_limit) -> str:
        """生成动态信息

        Args:
            data (dict): dict形式的动态数据.
            content_limit (int, optional): 内容字数限制.

        Returns:
            str: 动态信息
        """
        if not content_limit:
            content = data["content"]
        else:
            content = data["content"][:content_limit]

        return _OUTPUT_FORMAT.format(
            up_nickname=data["name"],
            up_dy_type=data["type_zh"],
            up_dy_content=str(content),
            up_dy_link=data['jump_url'],
        )

    async def add_sub(self, uid: int, group_id: int) -> str:
        up_nickname = await self.__get_up_nickname(uid)
        if not up_nickname:
            return f"无法获取id为 {uid} 的up主信息...操作失败了"

        query_result = await self.get_sub_list(uid, group_id)
        if query_result:
            return f"该up主 {up_nickname} 已在本群订阅列表中啦！"

        await self.__add_sub(uid, group_id)
        await self.update_sub(
            uid,
            group_id,
            {"up_nickname": up_nickname, "last_update": datetime.now(UTC)},
        )
        return f"成功订阅名为 {up_nickname} up主的动态～！"

    async def del_sub(self, uid: int, group_id: int) -> str:
        query_result = await self.get_sub_list(uid, group_id)
        if not query_result:
            return f"该uid: {uid} 未在本群订阅列表中啦！"

        await self.__del_sub(uid, group_id)
        return f"成功取消订阅uid为 {uid} up主的动态～！"
