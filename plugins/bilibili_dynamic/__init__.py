import re
import asyncio
from tabulate import tabulate
from datetime import datetime, timedelta, timezone as tz

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger

from nonebot import get_bot
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText
from nonebot.permission import Permission
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent

from ATRI.log import log
from ATRI.service import Service
from ATRI.utils import TimeDealer
from ATRI.permission import MASTER, ADMIN
from ATRI.message import MessageBuilder

from .data_source import BilibiliDynamicSubscriptor
from .model import BilibiliSubscription

__CONTENT_LIMIT = 500

plugin = Service(
    "b站动态订阅",
    "b站动态订阅助手~",
    "1.2.0",
    Service.ServiceType.SUBSCRIBE
).permission(ADMIN).main_cmd("/bd")
sub = BilibiliDynamicSubscriptor()

add_sub = plugin.cmd_as_group("add", "添加b站up主订阅")


@add_sub.handle()
async def _bd_add_sub(matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("bd_add_sub_id", args)


@add_sub.got("bd_add_sub_id", "up主id呢？速速")
async def _bd_deal_add_sub(
        event: GroupMessageEvent, _id: str = ArgPlainText("bd_add_sub_id")
):
    patt = r"^\d+$"
    if not re.match(patt, _id):
        await add_sub.reject("这似乎不是id呢，请重新输入:")

    __id = int(_id)
    group_id = event.group_id

    result = await sub.add_sub(__id, group_id)
    await add_sub.finish(result)


del_sub = plugin.cmd_as_group("del", "删除b站up主订阅")


@del_sub.handle()
async def _bd_del_sub(event: GroupMessageEvent):
    group_id = event.group_id

    query_result = await sub.get_sub_list(group_id=group_id)
    if not query_result:
        await del_sub.finish("本群还未订阅任何up主呢...")

    subs = list()
    for i in query_result:
        subs.append([i.up_nickname, i.uid])

    output = "本群订阅的up列表如下～\n" + tabulate(subs, headers=["up主", "uid"], tablefmt="plain")
    await del_sub.send(output)


@del_sub.got("bd_del_sub_id", "取消订阅的up主uid呢？速速\n(键入 1 以取消)")
async def _bd_deal_del_sub(
        event: GroupMessageEvent, _id: str = ArgPlainText("bd_del_sub_id")
):
    patt = r"^\d+$"
    if not re.match(patt, _id):
        await add_sub.reject("这似乎不是uid呢，请重新输入:")

    if _id == "1":
        await del_sub.finish("已取消操作～")

    __id = int(_id)
    group_id = event.group_id

    result = await sub.del_sub(__id, group_id)
    await del_sub.finish(result)


get_sub_list = plugin.cmd_as_group("list", "获取b站up主订阅列表", permission=Permission())


@get_sub_list.handle()
async def _bd_get_sub_list(event: GroupMessageEvent):
    group_id = event.group_id

    query_result = await sub.get_sub_list(group_id=group_id)
    if not query_result:
        await get_sub_list.finish("本群还未订阅任何up主呢...")

    subs = list()
    for i in query_result:
        raw_tm = (
                i.last_update.replace(tzinfo=tz(timedelta(hours=8))) + timedelta(hours=8)
        ).timestamp()
        tm = datetime.fromtimestamp(raw_tm).strftime("%m-%d %H:%M:%S")
        subs.append([i.up_nickname, tm])

    output = "本群订阅的up列表如下～\n" + tabulate(
        subs, headers=["up主", "最后更新时间"], tablefmt="plain"
    )
    await get_sub_list.finish(output)


limit_content = plugin.cmd_as_group("limit", "设置订阅内容字数限制", permission=MASTER)


@limit_content.handle()
async def _bd_get_limit(matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("bd_limit_int", args)


@limit_content.got("bd_limit_int", "要限制内容在多少字以内呢？(默认200，0=不限制)")
async def _td_deal_limit(
        event: GroupMessageEvent, _limit: str = ArgPlainText("bd_limit_int")
):
    patt = r"^\d+$"
    if not re.match(patt, _limit):
        await limit_content.reject("请键入阿拉伯数字:")

    global __CONTENT_LIMIT
    __CONTENT_LIMIT = int(_limit)
    await limit_content.finish(f"成功！订阅内容展示将限制在 {__CONTENT_LIMIT} 以内！")


tq = asyncio.Queue()


class BilibiliDynamicChecker(BaseTrigger):
    def get_next_fire_time(self, previous_fire_time, now):
        conf = plugin.conf()
        if conf.enabled:
            return now
        return None


async def bilibili_dynamic():
    try:
        all_dy = await sub.get_all_subs()
    except Exception:
        log.debug("b站订阅列表为空 跳过")
        return

    if tq.empty():
        for i in all_dy:
            await tq.put(i)
    m: BilibiliSubscription = tq.get_nowait()
    log.info(f"准备查询up主 {m.up_nickname} 的动态，队列剩余 {tq.qsize()}")

    ts = m.last_update.timestamp()
    info: dict = await sub.get_up_recent_dynamic(m.uid)
    result = sub.extract_dyanmic(info.get("items", []))
    if not result:
        log.warning(f"无法获取up主 {m.up_nickname} 的动态")
        return

    for i in result:
        i["name"] = m.up_nickname
        if ts < i["timestamp"]:
            content = sub.gen_output(i, __CONTENT_LIMIT)
            msg = MessageBuilder().text(content)
            _pic = i['pic']
            bot = get_bot()
            await sub.update_sub(
                m.uid,
                m.group_id,
                {
                    "last_update": TimeDealer(
                        float(i["timestamp"]), tz(timedelta(hours=8))
                    ).to_datetime(),
                },
            )
            for p in _pic:
                if p is None:
                    continue
                msg.image(file=p['url'])
            try:
                await bot.send_group_msg(group_id=m.group_id, message=msg)
            except Exception as e:
                await bot.send_group_msg(group_id=m.group_id, message=content)
                raise e from e


plugin.scheduler_jobs().add_job(
    bilibili_dynamic,
    "b站动态更新检查",
    AndTrigger([IntervalTrigger(seconds=300), BilibiliDynamicChecker()]),
    max_instances=3,  # type: ignore
    misfire_grace_time=60,  # type: ignore
)
