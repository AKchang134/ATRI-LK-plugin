import json
import contextlib

from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Arg
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11 import MessageSegment

from ATRI.service import Service
from ATRI.utils import request
from ATRI.message import MessageBuilder

plugin = Service(
    "点歌",
    "点歌插件",
    '0.2.2',
    Service.ServiceType.ENTERTAINMENT
)

dian_ge = plugin.on_command("点歌", "点一首歌")


@dian_ge.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    if args:
        matcher.set_arg("song_name", args)


@dian_ge.got("song_name", prompt="歌名是？")
async def _(msg: Message = Arg("song_name")):
    song_name = msg.extract_plain_text()
    song_id = await get_song_id(song_name)
    if not song_id:
        await dian_ge.finish(f"没有找到名为 {song_name} 的歌！")
    try:
        await dian_ge.finish(MessageSegment.music("163", song_id))
    except FinishedException as e:
        raise e from e
    except Exception:
        messages = MessageBuilder()
        info = await get_song_info(song_id)
        info = info['songs'][0]
        artists = []
        for artist in info['artists']:
            artists.append(artist['name'])
        messages.image(info['album']['picUrl'])
        messages.text(f"歌曲名:{info['name']}")
        messages.text(f"歌手:{','.join(artists)}")
        messages.text(f'专辑:{info['album']['name']}')
        messages.text(f"https://music.163.com/#/song?id={song_id}")
        await dian_ge.finish(messages)


async def search_song(song_name: str):
    r = await request.post(
        "http://music.163.com/api/search/get/",
        data={"s": song_name, "limit": 1, "type": 1, "offset": 0},
    )
    return None if r.status_code != 200 else json.loads(r.text)


async def get_song_id(song_name: str) -> int:
    if r := await search_song(song_name):
        with contextlib.suppress(KeyError):
            return r["result"]["songs"][0]["id"]
    return 0


async def get_song_info(song_id: int):
    r = await request.post(f"http://music.163.com/api/song/detail/?id={song_id}&ids=%5B{song_id}%5D")
    return None if r.status_code != 200 else json.loads(r.text)


# qq_dian_ge = plugin.on_command("qq点歌", "点一首歌", aliases={"QQ点歌", "QQ音乐", "qq音乐"})
#
#
# @qq_dian_ge.handle()
# async def _(matcher: Matcher, args: Message = CommandArg()):
#     if args:
#         matcher.set_arg("song_name", args)
#
#
# @qq_dian_ge.got("song_name", prompt="歌名是？")
# async def _(msg: Message = Arg("song_name")):
#     song_name = msg.extract_plain_text()
#     song_id = await get_qq_song_id(song_name)
#     if not song_id:
#         await qq_dian_ge.finish(f"没有找到名为 {song_name} 的歌！")
#     try:
#         await qq_dian_ge.finish(MessageSegment("music", {"type": "qq", "id": str(song_id[0])}))
#     except Exception:
#         # messages = MessageBuilder()
#         # info = await get_song_info(song_id)
#         # info = info['songs'][0]
#         # artists = []
#         # for artist in info['artists']:
#         #     artists.append(artist['name'])
#         # messages.image(info['album']['picUrl'])
#         # messages.text(f"歌曲名:{info['name']}")
#         # messages.text(f"歌手:{','.join(artists)}")
#         # messages.text(f'专辑:{info['album']['name']}')
#         # messages.text(f"https://music.163.com/#/song?id={song_id}")
#         await qq_dian_ge.finish(f"卡片发送失败...\nhttps://y.qq.com/n/ryqq/songDetail/{song_id[0]}")
#
#
# async def search_qq_song(song_name: str):
#     r = await request.get(
#         "https://c.y.qq.com/soso/fcgi-bin/client_search_cp",
#         params={"w": song_name, "format": "json", "n": 1},
#     )
#     return None if r.status_code != 200 else r.json()
#
#
# async def get_qq_song_id(song_name: str):
#     if r := await search_qq_song(song_name):
#         with contextlib.suppress(KeyError):
#             return r["data"]["song"]["list"][0]["songmid"], r["data"]["song"]["list"][0]["songid"]
#     return None
#
#
# data = {
#     "app": "com.tencent.music.lua",
#     "bizsrc": "qqconnect.sdkshare_music",
#     "config": {
#         "ctime": 1752645931,
#         "forward": 1,
#         "token": "c7033bb72b39afc747e3949912d51423",
#         "type": "normal"
#     },
#     "extra": {
#         "app_type": 1,
#         "appid": 100497308,
#         "msg_seq": 7527556957065404693,
#         "uin": 1161580563
#     },
#     "meta": {
#         "music": {
#             "app_type": 1,
#             "appid": 100497308,
#             "ctime": 1752645931,
#             "desc": "LBI利比（时柏尘）",
#             "jumpUrl": "https://i.y.qq.com/v8/playsong.html?platform=11&appshare=android_qq&appversion=14060508&hosteuin=oK6soK4Foe4soz**&songmid=002ulOzb02Xbdo&type=0&appsongtype=1&_wv=1&source=qq&ADTAG=qfshare",
#             "musicUrl": "http://c6.y.qq.com/rsc/fcgi-bin/fcg_pyq_play.fcg?songid=&songmid=002ulOzb02Xbdo&songtype=1&fromtag=50&uin=1161580563&code=7B068",
#             "preview": "https://y.gtimg.cn/music/photo_new/T002R150x150M000004CvHyt4dW543_2.jpg",
#             "tag": "QQ音乐",
#             "tagIcon": "https://p.qpic.cn/qqconnect/0/app_100497308_1626060999/100?max-age=2592000&t=0",
#             "title": "小城夏天",
#             "uin": 1161580563
#         }
#     },
#     "prompt": "[分享]小城夏天",
#     "ver": "0.0.0.1",
#     "view": "music"
# }
