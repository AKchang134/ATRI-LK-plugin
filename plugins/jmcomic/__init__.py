from random import choice
from jmcomic import MissingAlbumPhotoException

from nonebot.params import Depends, CommandArg
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.helpers import Cooldown

from ATRI.service import Service
from ATRI.message import file_msg
from ATRI.system.lkapi.bot.checker import is_lk_user, not_safe_mode

from .data_source import download

plugin = Service(
    "J漫画",
    "发送J漫画",
    "0.1.0",
    Service.ServiceType.FUNCTION
)

_lmt_notice = ["慢...慢一..点❤", "冷静1下", "歇会歇会~~", "呜呜...别急", "太快了...受不了", "不要这么快呀", "少冲点吧"]

jm = plugin.on_command("/jm", "下载漫画并以PDF方式发送，文件名需删除.del，10分钟cd")


@jm.handle([Cooldown(600, prompt=choice(_lmt_notice)), Depends(is_lk_user), Depends(not_safe_mode)])
async def _(args: Message = CommandArg()):
    c_id = args.extract_plain_text()
    if not c_id.isnumeric():
        await jm.finish("请输入数字id")
    try:
        path = download(c_id)
    except MissingAlbumPhotoException:
        await jm.finish("该漫画需要登录才能观看")
    with open(path, "rb") as file:
        data = file.read()
    await jm.finish(file_msg(f'{c_id}.pdf.del', data))
