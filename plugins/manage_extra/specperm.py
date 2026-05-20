from ATRI.permission import Permission, is_master, __init_permission

from nonebot.adapters import Event, Bot

from .utils import is_special_perm

class SpecPerm:
    __slots__ = ()

    async def __call__(self, bot: Bot, event: Event) -> bool:
        return is_special_perm(event) or is_master(bot, event)
    
__init_permission()
SPECPERM = Permission(SpecPerm()).set_name("SpecialPermission")
