import asyncio
import itertools
import os
import random
import re
import traceback

import qqbot
from qqbot.core.util.yaml_util import YamlUtil

from remake.life import Life
from typing import List, Tuple, Optional
from remake.talent import Talent
from qqbot import logger, AsyncMessageAPI, Message

test_config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yaml"))
state = 0
cur_life: Life
cur_talents: List[Talent]
cur_msg_api: AsyncMessageAPI
cur_msg: Message


def remake_reset():
    global state, cur_life, cur_talents, cur_msg_api, cur_msg
    state = 0
    cur_life = None
    cur_talents = None
    cur_msg_api = None
    cur_msg = None


async def send_msg(msg):
    send = qqbot.MessageSendRequest(msg, cur_msg.id)
    # 通过api发送回复消息
    await cur_msg_api.post_message(cur_msg.channel_id, send)


def get_cmd():
    cmd_match = re.fullmatch(r"^<@.*>\s(.*)", cur_msg.content)
    if cmd_match:
        return list(cmd_match.groups())[0]


async def remake():
    global state, cur_life, cur_talents, cur_msg_api, cur_msg
    if state == 0:
        cur_life = Life()
        cur_life.load()
        cur_talents = cur_life.rand_talents(10)
        msg = "请发送编号选择3个天赋，如“0 1 2”，或发送“随机”随机选择"
        des = "\n".join([f"{i}.{t}" for i, t in enumerate(cur_talents)])
        await send_msg(f"{msg}\n\n{des}")
        state = 1


async def hand_gift():
    global state, cur_life, cur_talents, cur_msg_api, cur_msg

    def conflict_talents() -> Optional[Tuple[Talent, Talent]]:
        for (t1, t2) in itertools.combinations(talents, 2):
            if t1.exclusive_with(t2):
                return t1, t2
        return None

    life_: Life = cur_life
    talents: List[Talent] = cur_talents
    cmd = get_cmd()
    match = re.fullmatch(r"\s*(\d)\s*(\d)\s*(\d)\s*", cmd)
    if match:
        nums = list(match.groups())
        nums = [int(n) for n in nums]
        nums.sort()
        if nums[-1] >= 10:
            await send_msg("请发送正确的编号")
            return

        talents_selected = [talents[n] for n in nums]
        ts = conflict_talents()
        if ts:
            await send_msg(f"你选择的天赋“{ts[0].name}”和“{ts[1].name}”不能同时拥有，请重新选择")
            return
    elif cmd == "随机":
        while True:
            nums = random.sample(range(10), 3)
            nums.sort()
            talents_selected = [talents[n] for n in nums]
            if not conflict_talents():
                break
    elif re.fullmatch(r"[\d\s]+", cmd):
        await send_msg("请发送正确的编号，如“0 1 2”")
        return
    else:
        await send_msg("人生重开已取消")
        remake_reset()
        return

    life_.set_talents(talents_selected)
    cur_talents = talents_selected

    msg = (
        "请发送4个数字分配“颜值、智力、体质、家境”4个属性，如“5 5 5 5”，或发送“随机”随机选择；"
        f"可用属性点为{life_.total_property()}，每个属性不能超过10"
    )
    await send_msg(msg)
    state = 2


async def hand_prop():
    global state, cur_life, cur_talents, cur_msg_api, cur_msg
    life_: Life = cur_life
    talents: List[Talent] = cur_talents
    total_prop = life_.total_property()
    cmd = get_cmd()

    match = re.fullmatch(r"\s*(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s*", cmd)
    if match:
        nums = list(match.groups())
        nums = [int(n) for n in nums]
        if sum(nums) != total_prop:
            await send_msg(f"属性之和需为{total_prop}，请重新发送")
            return
        elif max(nums) > 10:
            await send_msg("每个属性不能超过10，请重新发送")
            return
    elif cmd == "随机":
        half_prop1 = int(total_prop / 2)
        half_prop2 = total_prop - half_prop1
        num1 = random.randint(0, half_prop1)
        num2 = random.randint(0, half_prop2)
        nums = [num1, num2, half_prop1 - num1, half_prop2 - num2]
        random.shuffle(nums)
    elif re.fullmatch(r"[\d\s]+", cmd):
        await send_msg("请发送正确的数字，如“5 5 5 5”")
        return
    else:
        await send_msg("人生重开已取消")
        remake_reset()
        return

    prop = {"CHR": nums[0], "INT": nums[1], "STR": nums[2], "MNY": nums[3]}
    life_.apply_property(prop)

    await send_msg("你的人生正在重开...")

    msgs = [
        "已选择以下天赋：\n" + "\n".join([str(t) for t in talents]),
        "已设置如下属性：\n" + f"颜值{nums[0]} 智力{nums[1]} 体质{nums[2]} 家境{nums[3]}",
    ]
    try:
        life_msgs = []
        for s in life_.run():
            life_msgs.append("\n".join(s))
        n = 5
        life_msgs = [
            "\n\n".join(life_msgs[i: i + n]) for i in range(0, len(life_msgs), n)
        ]
        msgs.extend(life_msgs)
        msgs.append(life_.gen_summary())
        for msg in msgs:
            await send_msg(msg)
            await asyncio.sleep(2)
    except:
        logger.warning(traceback.format_exc())
        await send_msg("你的人生重开失败")
    remake_reset()


async def _message_handler(event, message: qqbot.Message):
    """
    定义事件回调的处理

    :param event: 事件类型
    :param message: 事件对象（如监听消息是Message对象）
    """
    global cur_msg_api, cur_msg
    # 打印返回信息
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)
    cur_msg_api = qqbot.AsyncMessageAPI(t_token, False)
    cur_msg = message
    if state == 0 and ("remake" or "重开" in message.content):
        await remake()
    elif state == 1:
        await hand_gift()
    elif state == 2:
        await hand_prop()
    elif "壁纸" not in message.content:
        send = qqbot.MessageSendRequest("不晓得你在说些啥子几把", message.id)
        # 通过api发送回复消息
        await cur_msg_api.post_message(message.channel_id, send)


if __name__ == "__main__":
    # async的异步接口的使用示例
    t_token = qqbot.Token(test_config["token"]["appid"], test_config["token"]["token"])
    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    qqbot.async_listen_events(t_token, False, qqbot_handler)
