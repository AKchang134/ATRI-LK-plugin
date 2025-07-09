from random import choice
from typing import List
import aiofiles

from nonebot import get_bots
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown

from ATRI import TEMP_DIR
from ATRI.permission import ADMIN
from ATRI.service import Service
from ATRI.log import log
from ATRI.utils import request
from ATRI.utils.img_editor import get_image_bytes
from ATRI.utils.model import BaseModel
from ATRI.configs import PluginConfig
from ATRI.exceptions import str_traceback

plugin = Service(
    "每日新闻",
    "每日新闻与摸鱼日历相关的服务",
    "1.3.0",
    Service.ServiceType.FUNCTION
)

# url = "http://dwz.2xb.cn/zaob"
url = 'https://api.southerly.top/api/60s?format=json'
moyu = 'https://api.southerly.top/api/moyu'
_lmt_notice = ["慢...慢一..点❤", "冷静1下", "歇会歇会~~", "呜呜...别急", "太快了...受不了", "不要这么快呀"]


class DailyNewsConfig(BaseModel):
    groups: List[str] = []
    moyu: List[str] = []
    hour: int = 8
    minute: int = 0


config_manage = PluginConfig(plugin.service, DailyNewsConfig)

config: DailyNewsConfig = config_manage.config()

today_news = plugin.on_command(cmd='今日新闻', docs="查看今日新闻")


@today_news.handle([Cooldown(60 * 60, prompt=choice(_lmt_notice))])
async def _():
    _, news = await get_news()
    await today_news.finish(news)


today_moyu = plugin.on_command(cmd='摸鱼日历', docs="查看今日摸鱼日历")


@today_moyu.handle([Cooldown(60 * 60, prompt=choice(_lmt_notice))])
async def _():
    await today_moyu.finish(await get_moyu())


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


moyu_sub = plugin.on_command(cmd="摸鱼日历订阅", docs="管理本群的摸鱼日历订阅", permission=ADMIN)


@moyu_sub.handle()
async def _(event: GroupMessageEvent):
    group_id = str(event.group_id)
    if group_id in config.moyu:
        config.moyu.remove(group_id)
        config_manage.change_config(config)
        await moyu_sub.finish("本群摸鱼日历订阅已关闭")
    else:
        config.moyu.append(group_id)
        config_manage.change_config(config)
        await moyu_sub.finish("本群摸鱼日历新闻订阅已开启")


async def daily_job():
    _, message = await get_news()
    mo_yu = await get_moyu()
    for bot in get_bots().values():
        if type(bot) is Bot:
            group_list = await bot.get_group_list()
            for group in group_list:
                group_id = str(group["group_id"])
                if group_id in config.groups:
                    await bot.send_group_msg(group_id=group_id, message=Message().append(message))
                if group_id in config.moyu:
                    await bot.send_group_msg(group_id=group_id, message=Message().append(mo_yu))


plugin.scheduler_jobs().add_job(daily_job, "新闻订阅", 'cron', hour=config.hour, minute=config.minute)


async def get_news() -> tuple[bool, MessageSegment]:
    path = TEMP_DIR / "news.png"
    retry = 0
    while retry < 5:
        try:
            resp = await request.get(url)
            resp.raise_for_status()
            url_json = resp.json()
            # image_url = str(url_json["imageUrl"])
            image_url = str(url_json["data"]["image"])
            resp = await request.get(image_url)
            resp.raise_for_status()
            content = resp.content
            async with aiofiles.open(path, "wb") as wf:
                await wf.write(content)
            return True, MessageSegment.image(get_image_bytes(path))
        except Exception as e:
            log.warning(f"第{retry + 1}次获取新闻错误:\n{str_traceback(e)}")
            retry += 1
    return False, MessageSegment.text(text="很遗憾，获取今日份新闻失败了捏")


async def get_moyu() -> MessageSegment:
    path = TEMP_DIR / "moyu.png"
    retry = 0
    while retry < 5:
        try:
            resp = await request.get(moyu)
            resp.raise_for_status()
            content = resp.content
            async with aiofiles.open(path, "wb") as wf:
                await wf.write(content)
            return MessageSegment.image(get_image_bytes(path))
        except Exception as e:
            log.warning(f"第{retry + 1}次获取摸鱼日历错误:\n{str_traceback(e)}")
            retry += 1
    return MessageSegment.text(text="很遗憾，今日份的摸鱼日历获取失败了捏")
