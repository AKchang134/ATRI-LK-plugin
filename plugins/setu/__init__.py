import re
from random import choice

from nonebot.params import ArgPlainText
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, ActionFailed, GroupMessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown

from ATRI import IMG_DIR
from ATRI.service import Service
from ATRI.utils.img_editor import get_image_bytes
from ATRI.system.lkbot.util import lk_util

from .data_source import Setu

plugin = Service("涩图").document("hso!").main_cmd("/setu").type(Service.ServiceType.ENTERTAINMENT).version("1.1.2")

random_setu = plugin.on_command(
    "来张涩图", "来张随机涩图，冷却2分钟", aliases={"涩图来", "来点涩图", "来份涩图"}, priority=5
)


@random_setu.handle([Cooldown(120, prompt="2分钟冷却中")])
async def _(bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent) and lk_util.is_safe_mode_group(event.group_id):
        await random_setu.finish(MessageSegment.image(get_image_bytes(f'{IMG_DIR}/damiesese.jpg')))
    setu, setu_data = await Setu.new()
    setu_info = f"Title: {setu_data.title}\nPid: {setu_data.pid}"
    await bot.send(event, setu_info)
    try:
        await random_setu.send(setu)
        await random_setu.send(f"url: {setu_data.url}")
    except Exception:
        await random_setu.send("hso (发不出")
        await random_setu.send(f"自己动手: {setu_data.url}")


@random_setu.got("r_rush_after_think", prompt="看完不来点感想么-w-")
async def _(think: str = ArgPlainText("r_rush_after_think")):
    is_repo = will_think(think)
    if not is_repo:
        await random_setu.finish()
    else:
        await random_setu.finish(is_repo)


tag_setu = plugin.on_regex(r"来[张点丶份](.*?)的?[涩色🐍]图", "根据提供的tag查找涩图，冷却2分钟", priority=6)


@tag_setu.handle([Cooldown(120, prompt="2分钟冷却中")])
async def _(bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent) and lk_util.is_safe_mode_group(event.group_id):
        await tag_setu.finish(MessageSegment.image(get_image_bytes(f'{IMG_DIR}/damiesese.jpg')))
    msg = str(event.get_message()).strip()
    pattern = r"来[张点丶份](.*?)的?[涩色🐍]图"
    tag = re.findall(pattern, msg)[0]
    setu, setu_data = await Setu.new(tag)
    if not setu_data.url:
        await tag_setu.finish("没有合适的涩图呢...")
    setu_info = f"Title: {setu_data.title}\nPid: {setu_data.pid}"
    await bot.send(event, setu_info)

    try:
        await random_setu.send(setu)
    except ActionFailed:
        await random_setu.send("hso (发不出")
        await random_setu.send(f"自己动手: {setu_data.url}")


@tag_setu.got("t_rush_after_think", prompt="看完不来点感想么-w-")
async def _(think: str = ArgPlainText("t_rush_after_think")):
    is_repo = will_think(think)
    if not is_repo:
        await random_setu.finish()
    else:
        await random_setu.finish(is_repo)


_ag_l = ["涩图来", "来点涩图", "来份涩图"]
_ag_patt = r"来[张点丶份](.*?)的[涩色🐍]图"

_nice_patt = r"[hH好][sS涩色][oO哦]|[嗯恩摁社蛇🐍射]了|(硬|石更)了|[牛🐂][牛🐂]要炸了|[炼恋]起来|开?导"
_nope_patt = r"不够[涩色]|就这|不行|不彳亍|一般|这也[是叫算]|[?？]|就这|爬|爪巴"
_again_patt = r"再来一张|不够"

_nice_repo = ["w", "好诶！", "ohh", "(///w///)", "🥵", "我也"]
_nope_repo = ["那你来发", "爱看不看", "你看不看吧", "看这种类型的涩图，是一件多么美妙的事情"]
_again_repo = ["没了...", "自己找去"]


def will_think(msg: str) -> str:
    if msg in _ag_l:
        return str()

    ag_jud = re.findall(_ag_patt, msg)
    if ag_jud:
        return str()

    nice_jud = re.findall(_nice_patt, msg)
    nope_jud = re.findall(_nope_patt, msg)
    again_jud = re.findall(_again_patt, msg)

    if nice_jud:
        return choice(_nice_repo)
    elif nope_jud:
        return choice(_nope_repo)
    elif again_jud:
        return choice(_again_repo)
    else:
        return str()
