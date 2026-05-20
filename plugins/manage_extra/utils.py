from nonebot.adapters import Event, Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .config import config

from hashlib import md5 as _md5
import asyncio


def md5(text: str | int):
    return _md5(str(text).encode("utf-8")).hexdigest()


def is_special_perm(event: Event | GroupMessageEvent):
    try: 
        _id = event.get_user_id()
    except:
        return False
    
    sp_users = config.special_perms

    return _id in sp_users


async def is_bot_group_admin(event: GroupMessageEvent, bot: Bot):
    try:
        bot_info = await bot.get_group_member_info(
            group_id=event.group_id, user_id=int(bot.self_id)
        )
        return bot_info.get("role", "member") != "member"
    except Exception:
        return False


async def get_hist_msg_grp(bot: Bot, group_id: int, start_ts: int, end_ts: int):
    PAGE_SIZE = 100
    collected_messages = []
    current_seq = None

    while True:
        params = {
            "group_id": group_id,
            "reverse_order": True,
            "count": PAGE_SIZE
        }
        if current_seq is not None:
            params["message_seq"] = current_seq

        res = await bot.call_api("get_group_msg_history", **params)

        messages = res.get("messages", [])
        if not messages: break

        newest_msg = messages[0]
        oldest_msg = messages[-1]

        for msg in messages:
            t = msg.get("time", 0)
            if start_ts <= t < end_ts:
                if not msg in collected_messages:
                    collected_messages.append(msg)

        oldest_time = oldest_msg.get("time", 0)
        if oldest_time < start_ts: break

        next_seq = newest_msg.get("message_seq")
        if next_seq is None: break

        if current_seq is not None and next_seq == current_seq: break

        current_seq = next_seq
        await asyncio.sleep(config.utils_config["get_history_interval"])

    return collected_messages
