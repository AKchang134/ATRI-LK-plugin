from random import choice
from os import getcwd
from datetime import datetime, timedelta, timezone, date
from typing import Optional
import time

from ATRI.service import Service
from ATRI.system.lkbot.util import BaseFunc
from ATRI.system.lkbot.util import lk_util
from ATRI.permission import ADMIN, MASTER
from ATRI.dir import TEMP_DIR

from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.helpers import Cooldown
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

from .utils import md5, get_hist_msg_grp, is_special_perm, is_bot_group_admin
from .specperm import SPECPERM
from .config import config


plugin = Service(
    "Manage-Extra",
    "管理功能扩展. 请根据需要调整执行命令所需的权限等级. ",
    "1.0.0",
    Service.ServiceType.FUNCTION
)

_lmt_notice = ["慢...慢一..点❤", "冷静1下", "歇会歇会~~", "呜呜...别急", "太快了...受不了", "不要这么快呀"]



mute_cmd = plugin.on_command("mute", "禁言指定成员. 使用时需 @ 亚托莉. \n用法: /mute <@user>(<seconds>|unmute)\n当 <seconds> 参数为 0 或字面量为 unmute 时，解除禁言. \n显然该命令不可对主人或亚托莉自己生效. ", permission = ADMIN)

@mute_cmd.handle([Cooldown(1, prompt=choice(_lmt_notice))])
async def handle_mute(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not event.to_me:
        return
    
    if len(args) != 2:
        await mute_cmd.finish("参数填错了啦...", at_sender=True)

    target_at = args[0]
    try:
        dur_arg = args[1].data['text'].strip()
        if dur_arg == "unmute": duration = 0
        else: duration = int(dur_arg)
    except ValueError:
        await mute_cmd.finish("时长参数应当为以秒为单位的数字或字面量 unmute 才行哦！", at_sender=True)

    if target_at.type != "at":
        await mute_cmd.finish("请正确 @ 要禁言的成员呢...", at_sender=True)
    try:
        target_qq = int(target_at.data['qq'])
    except (IndexError, ValueError):
        await mute_cmd.finish("呜...看不懂 @ 的用户是谁呢，请确保使用 QQ 自带的 @ 功能哦", at_sender=True)
        return
    
    bot_qq = int(bot.self_id)

    if target_qq == bot_qq:
        await mute_cmd.finish("不能给自己塞上口球啦...")
        return
    
    if BaseFunc.is_master(target_qq):
        await mute_cmd.finish("才不会给主人塞上口球呢！")
        return

    await bot.set_group_ban(
        group_id=event.group_id,
        user_id=target_qq,
        duration=duration
    )

    return





set_admin_cmd = plugin.on_command("set_admin", "将指定成员设为或取消管理员. 使用时需 @ 亚托莉. \n用法: /set_admin <@user> (True|False). \n显然该命令不可对亚托莉自己生效. ", permission = ADMIN)

@set_admin_cmd.handle([Cooldown(1, prompt=choice(_lmt_notice))])
async def handle_set_admin(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not event.to_me:
        return
    
    if len(args) != 2:
        await set_admin_cmd.finish("参数填错了啦...", at_sender=True)
        return

    target_seg = args[0]
    if target_seg.type != "at":
        await set_admin_cmd.finish("请正确 @ 要设置为管理员的成员呢...", at_sender=True)
        return

    try:
        target_qq = int(target_seg.data["qq"])
    except (KeyError, ValueError):
        await set_admin_cmd.finish("呜...看不懂 @ 的用户是谁呢，请确保使用 QQ 自带的 @ 功能哦", at_sender=True)
        return

    bot_id = int(bot.self_id)
    if target_qq == bot_id:
        await set_admin_cmd.finish("不能自己操作自己的权限哦！")

    operation = False

    if args[1].data["text"].strip() == "True":
        operation = True
    elif args[1].data["text"].strip() != "False":
        await set_admin_cmd.finish("字面量填错了呢...")
        return
    
    if BaseFunc.is_master(target_qq) and not operation:
        await set_admin_cmd.finish("不能取消主人的管理员身份啦...")
        return

    await bot.set_group_admin(
        group_id=event.group_id,
        user_id=target_qq,
        enable=operation
    )

    await set_admin_cmd.finish("成功将 " + MessageSegment.at(target_qq) + f" 的管理员权限设为 {str(operation)} 了呢! ")
    return




set_title_cmd = plugin.on_command(
    "set_title",
    "设置或清除群成员头衔. 使用时需 @ 亚托莉. \n用法: /set_title <@user> [<text>]. \n<text> 参数长度不得大于 6. 为空时，清除群成员头衔. ",
    permission = ADMIN
)

@set_title_cmd.handle([Cooldown(1, prompt=choice(_lmt_notice))])
async def handle_set_title(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not event.to_me:
        return
    
    if len(args) < 1 or len(args) > 2:
        await set_title_cmd.finish("参数填错了啦...", at_sender=True)
        return

    target_seg = args[0]
    if target_seg.type != "at":
        await set_title_cmd.finish("请正确 @ 要设置头衔的成员呢...", at_sender=True)
        return

    try:
        target_qq = int(target_seg.data["qq"])
    except (KeyError, ValueError):
        await set_title_cmd.finish("呜...看不懂 @ 的用户是谁呢，请确保使用 QQ 自带的 @ 功能哦", at_sender=True)
        return

    title = args[1].data["text"].strip() if len(args) >= 2 else ""

    if len(title) > 6:
        await set_title_cmd.finish("头衔内容不能超过6个字符呢...", at_sender=True)
        return
    
    if BaseFunc.is_master(target_qq) and title == '':
        await set_title_cmd.finish("不能清除主人的头衔啦...", at_sender=True)
        return

    await bot.set_group_special_title(
        group_id=event.group_id,
        user_id=target_qq,
        special_title=title,
        duration=-1
    )
    if title:
        await set_title_cmd.finish("成功授予了 " + MessageSegment.at(target_qq) + f"「{title}」头衔了呢~", at_sender=True)
    else:
        await set_title_cmd.finish(MessageSegment.at(target_qq) + " 的头衔被清除了呢...")
    return






all_group_sign_cmd = plugin.on_command("all_group_sign", "在所有亚托莉所在群聊打卡. 使用时需 @ 亚托莉. ", permission = MASTER)

@all_group_sign_cmd.handle()
async def handle_all_group_sign(bot: Bot, event: MessageEvent):
    if not event.to_me:
        return
    
    __group_list = await bot.get_group_list()
    group_list = []
    for __ in __group_list:
        group_list.append(__["group_id"])

    failed_cnt = 0

    for __ in  group_list:
        params = {"group_id": __}
        try:
            await bot.call_api("send_group_sign", **params)
        except ActionFailed:
            failed_cnt += 1

    await all_group_sign_cmd.finish(f"已尝试在所有所在群聊打卡~共 {len(group_list)} 个，失败 {failed_cnt} 个")
    return
    







change_user_name = plugin.on_command("change_username", "增强版 /强制改名 命令，支持根据 QQ 号改名. \n用法: /change_user <@user>|<userId> <name>", permission = MASTER)
@change_user_name.handle()
async def handle_chg_username(args: Message = CommandArg()):
    target_id = None
    name = None
    if len(args) == 1:
        if args[0].type == "text":
            __args = args[0].data["text"].strip()
            _arg_check = __args.split()
            target_id = _arg_check[0]
            try:
                __ = int(target_id)
            except:
                await change_user_name.finish("参数错了啦...")
                return
            name = __args[len(_arg_check[0]):].strip()
            if not name:
                await change_user_name.finish("名字不能为空哦")
                return
        else:
            await change_user_name.finish("参数错了啦...")
            return
    else:
        if args[0].type == "at":
            target_id = args[0].data["qq"]
        else:
            await change_user_name.finish("参数错了啦...")
            return
        name = args[1].data["text"].strip()

    _, res = lk_util.user_change_name(target_id, name)
    await change_user_name.finish(res)
    return








__group_todo_acceptable_args = ["set", "finish", "complete", "cancel", "unset"]
__group_todo_cmd_docs_args = ''
for __ in range(len(__group_todo_acceptable_args)):
    if __: __group_todo_cmd_docs_args += '|'
    __group_todo_cmd_docs_args += __group_todo_acceptable_args[__]

group_todo_cmd = plugin.on_command("group_todo", f"群待办相关操作. \n用法: /group_todo ({__group_todo_cmd_docs_args}). \n使用时应引用消息并 @ 亚托利. \n字面量为 set 时，将引用的消息设为群待办. \n字面量为 finish 或 complete 时，将引用的消息对应的群待办标记为完成. \n字面量为 unset 或 cancel 时，将引用的消息对应的群待办取消. ", permission = ADMIN)

@group_todo_cmd.handle()
async def handle_group_todo(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not event.to_me: return

    if len(args) != 1:
        await group_todo_cmd.finish("字面量错了啦...")
        return
    
    if not args[0].type == "text":
        await group_todo_cmd.finish("字面量错了啦...")
        return
    
    __ = args[0].data["text"].strip()
    if not __ in __group_todo_acceptable_args:
        await group_todo_cmd.finish("字面量错了啦...")
        return
    
    reply_msg_id: Optional[int] = None
    if event.reply:
        reply_msg_id = event.reply.message_id

    if not reply_msg_id:
        await group_todo_cmd.finish("消息未被正确引用或未被记录呢...")
        return

    params = {
        "group_id": event.group_id,
        "message_id": str(reply_msg_id)
    }

    if __ == "set":
        if not await is_bot_group_admin(event, bot):
            await group_todo_cmd.finish("咱没有权限的啦...")
            return
        
        try:
            await bot.call_api("set_group_todo", **params)
            await group_todo_cmd.finish("成功设置了群待办~我果然还是高性能的吧~！")
            return
        except ActionFailed:
            await group_todo_cmd.finish("呜...失败了呢...")
            return
    elif __ == "finish" or __ == "complete":
        if (not is_special_perm(event)) and not lk_util.is_master(event.user_id):
            await group_todo_cmd.finish("权限不够啦，只有 SPECPERM 权限可以使用该字面量哦")
            return
        try:
            await bot.call_api("complete_group_todo", **params)
            await group_todo_cmd.finish("成功完成了群待办~我果然还是高性能的吧~！")
            return
        except ActionFailed:
            await group_todo_cmd.finish("失败了呢...可能这条消息并不是群待办呢...")
            return
    elif __ == "cancel" or __ == "unset":
        if not is_bot_group_admin(event, bot):
            await group_todo_cmd.finish("咱没有权限的啦...")
            return

        try:
            await bot.call_api("cancel_group_todo", **params)
            await group_todo_cmd.finish("成功取消了群待办~我果然还是高性能的吧~！")
            return
        except ActionFailed:
            await group_todo_cmd.finish("失败了呢...可能这条消息并不是群待办呢...")
            return







TIMEZONE = timezone(timedelta(hours=8))

get_msg_cmd = plugin.on_command(
    "get_msg",
    "获取指定时间范围内的消息. \n"
    "用法: /get_msg <startTime> <endTime> [True|False]. \n"
    "参数 <startTime> 和 <endTime> 的格式应为 YYYY-mm-DD HH:MM:SS. \n"
    "当未填写字面量或其值为 False 时，将结果前 10 条发送至聊天；否则将完整查询结果写入为一个文本文件并发送至聊天. "
)

@get_msg_cmd.handle([Cooldown(30, prompt = choice(_lmt_notice))])
async def handle_get_msg(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    group_id = event.group_id

    raw = arg.extract_plain_text().strip()
    if not raw:
        await get_msg_cmd.finish("要正确填写参数啦...")

    as_file = False

    __ = raw.split(' ')

    if __[len(__) - 1] == "True":
        as_file = True
        raw = raw[:-5]
    elif __[len(__) - 1] == "False": raw = raw[:-6]

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]

    def parse_time(s: str):
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=TIMEZONE)
            except ValueError:
                continue
        raise ValueError("unaccepted argument")

    parts = raw.split()
    success = False
    for i in range(1, len(parts) + 1):
        start_candidate = " ".join(parts[:i])
        end_candidate = " ".join(parts[i:]) if i < len(parts) else ""
        try:
            start_dt = parse_time(start_candidate)
            end_dt = parse_time(end_candidate)
            success = True
            break
        except ValueError:
            continue

    if not success:
        await get_msg_cmd.finish("要正确填写参数啦...")
        return

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    if start_ts >= end_ts:
        await get_msg_cmd.finish("结束时间要晚于起始时间啦...")
        return

    await get_msg_cmd.send(f"开始尝试拉取 {start_dt.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_dt.strftime('%Y-%m-%d %H:%M:%S')} 的消息，稍等哦~")

    collected_messages = await get_hist_msg_grp(bot, group_id, start_ts, end_ts)

    count = len(collected_messages)
    if count == 0:
        await get_msg_cmd.finish("没有找到符合条件的历史消息呢...")
        return
    
    collected_messages.sort(key = lambda __: __.get("time", 0))

    if as_file:
        await get_msg_cmd.send(f"成功找到了 {count} 条消息，正在尝试写入到文件并上传~")
        __save_path = getcwd() / TEMP_DIR / "akcs_extra" / "get_msg"
        __save_path.mkdir(exist_ok=True)
        __save_path = __save_path / (str(group_id) + '_' + md5(str(start_ts) + '-' + str(end_ts)) + ".txt")
        
        with open(__save_path, 'w', encoding = "utf-8") as f:
            for msg in collected_messages:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.get('time', 0)))}] {msg.get('sender', {}).get('nickname', 'Unknown User')}: {str(msg.get('message', ''))} \n")
            f.close()

        params = {
            "group_id": group_id,
            "file": str(__save_path),
            "name": f"history_{group_id}_{time.strftime('%Y%m%d_%H_%M_%S', time.localtime(start_ts))}-{time.strftime('%Y%m%d_%H_%M_%S', time.localtime(end_ts))}.txt"
        }

        await bot.call_api("upload_group_file", **params)
        await get_msg_cmd.finish("上传完成~我果然还是高性能的吧~！")
        return
    else:
        preview = "\n".join([
            f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.get('time', 0)))}] {msg.get('sender', {}).get('nickname', 'Unknown User')}: {str(msg.get('message', ''))[:40]}..."
            for msg in collected_messages[:10]
        ])
        await get_msg_cmd.finish(f"成功找到了 {count} 条消息，我果然还是高性能的吧~！ \n{preview}")
    return







batch_recall_cmd = plugin.on_command("batch_recall", "按时间段批量撤回消息，可指定仅撤回指定成员的消息，使用时需 @ 亚托莉. \n用法: /batch_recall <startTime> <endTime> [<userId1>] [<userId2>] [<userId3>] ... \n<userId> 参数可填多个，用于指定撤回的成员. \n例: /batch_recall 1970-01-01 00:00:00 1970-01-01 00:01:00 10001 10002. ", aliases={"br"}, permission = ADMIN)

@batch_recall_cmd.handle([Cooldown(30, prompt=choice(_lmt_notice))])
async def handle_batch_recall(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if not event.to_me: return

    group_id = event.group_id

    raw = args.extract_plain_text().strip()
    if not raw:
        await batch_recall_cmd.finish("要正确填写参数啦...")

    words = raw.split()
    recall_users = []
    time_words = []
    for w in words:
        if w.isdigit() and 5 <= len(w) <= 11:
            recall_users.append(w)
        else:
            time_words.append(w)

    if not time_words:
        await batch_recall_cmd.finish("不是有效的时间参数啦...")

    time_str = " ".join(time_words)

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]

    def parse_time(s: str):
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=TIMEZONE)
            except ValueError:
                continue
        raise ValueError("unaccepted argument")

    parts = time_str.split()
    success = False
    start_dt = None
    end_dt = None
    for i in range(1, len(parts) + 1):
        start_candidate = " ".join(parts[:i])
        end_candidate = " ".join(parts[i:]) if i < len(parts) else ""
        if not end_candidate:
            continue
        try:
            start_dt = parse_time(start_candidate)
            end_dt = parse_time(end_candidate)
            success = True
            break
        except ValueError:
            continue

    if not success:
        await batch_recall_cmd.finish("要正确填写参数啦...")
        return

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    if start_ts >= end_ts:
        await batch_recall_cmd.finish("结束时间要晚于起始时间啦...")
        return
    
    __recall_users = "所有用户"
    for __ in range(len(recall_users)):
        if __ == 0: __recall_users += ' '
        elif __ < len(recall_users): __recall_users += '，'
        __recall_users += f"{str(recall_users[__])}"

    if recall_users: __recall_users += ' '

    await batch_recall_cmd.send(f"开始尝试拉取并撤回 {start_dt.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_dt.strftime('%Y-%m-%d %H:%M:%S')} {__recall_users}发送的消息，稍等哦~")

    msgs = await get_hist_msg_grp(bot, group_id, start_ts, end_ts)

    msg_ids = []
    for __ in msgs:
        if __ and type(__) == dict:
            _user = str(__.get("user_id", None))
            _ = __.get("message_id", None)
            _data_check = __.get("message", None)
            if _ and _user and _data_check:
                if lk_util.is_master(_user) and not lk_util.is_master(event.user_id): continue
                if recall_users:
                    if _user in recall_users:
                        msg_ids.append(_)
                else: msg_ids.append(_)
    
    msg_lmt = config.batch_recall_config["message_limit"]
    if len(msg_ids) > msg_lmt: msg_ids = msg_ids[:msg_lmt - 1]

    if not msg_ids:
        await batch_recall_cmd.finish("没有满足条件的可撤回的消息呢...")
        return
    
    await batch_recall_cmd.send(f"成功拉取到了 {len(msgs)} 条消息，满足条件的可撤回消息数为 {len(msg_ids)}，开始尝试批量撤回消息，稍等哦~")

    failed_cnt = 0

    for __ in msg_ids:
        try:
            await bot.delete_msg(message_id=__)
        except ActionFailed:
            failed_cnt += 1

    fin_msg = "已尝试撤回所有满足条件的可撤回消息~"
    fin_msg += f"但有 {failed_cnt} 条失败惹..." if failed_cnt else "我果然还是高性能的吧~！"

    await batch_recall_cmd.finish(fin_msg)
    return
