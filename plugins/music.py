import json
import contextlib

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
    '0.2.1',
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
