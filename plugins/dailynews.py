from random import choice
from typing import List

from nonebot import get_bots
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown

from ATRI import driver
from ATRI.permission import ADMIN
from ATRI.service import Service
from ATRI.utils.apscheduler import scheduler
from ATRI.log import log
from ATRI.utils import request
from ATRI.utils.model import BaseModel
from ATRI.configs import PluginConfig

plugin = Service("每日新闻").document("订阅每日新闻服务").type(Service.ServiceType.FUNCTION).version("1.1.1")

url = "http://dwz.2xb.cn/zaob"
_lmt_notice = ["慢...慢一..点❤", "冷静1下", "歇会歇会~~", "呜呜...别急", "太快了...受不了", "不要这么快呀"]


class NewsGroupConfig(BaseModel):
    groups: List[str] = []


config_manage = PluginConfig("每日新闻", NewsGroupConfig)

config: NewsGroupConfig = config_manage.config()

today_news = plugin.on_command(cmd='今日新闻', docs="查看今日新闻")


@today_news.handle([Cooldown(60 * 60, prompt=choice(_lmt_notice))])
async def _():
    await today_news.finish(await get_news())


news_sub = plugin.on_command(cmd="每日新闻订阅", docs="管理本群的新闻订阅", permission=ADMIN)


@news_sub.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)
    if group_id in config.groups:
        config.groups.remove(group_id)
        config_manage.change_config(config)
        await news_sub.finish("本群每日新闻订阅已关闭")
    else:
        config.groups.append(group_id)
        config_manage.change_config(config)
        await news_sub.finish("本群每日新闻订阅已开启")


async def daily_job():
    message = await get_news()
    for bot in get_bots().values():
        if type(bot) is Bot:
            group_list = await bot.get_group_list()
            for group in group_list:
                group_id = str(group["group_id"])
                if group_id in config.groups:
                    await bot.send_group_msg(group_id=group_id, message=Message().append(message))


driver().on_startup(lambda: scheduler.add_job(daily_job, 'cron', hour=7, minute=0))


async def get_news() -> MessageSegment:
    try:
        resp = await request.get(url)
        resp.raise_for_status()
        url_json = resp.json()
        image_url = str(url_json["imageUrl"])
        return MessageSegment.image(file=image_url)
    except Exception as e:
        log.error(f"{e}:{e.args}")
        return MessageSegment.text(text="很遗憾，获取今日新闻失败了捏")
