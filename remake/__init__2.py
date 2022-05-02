import os
import re

import qqbot
from remake.life2 import Life
from qqbot.core.util.yaml_util import YamlUtil
from construct.event import Event

from qqbot import AsyncMessageAPI, Message

test_config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yaml"))
state = 0

cur_msg_api: AsyncMessageAPI
life_map = {}


async def send_sample_msg(msg, message):
    send = qqbot.MessageSendRequest(msg, message.id)
    # 通过api发送回复消息
    await cur_msg_api.post_message(message.channel_id, send)


def get_cmd(content):
    cmd_match = re.fullmatch(r"^<@.*>\s(.*)", content)
    if cmd_match:
        return list(cmd_match.groups())[0]


async def remake(author, message):
    life = life_map.get(author.id)
    # 如果为空 则新建 否则直接从全局中获取
    if life is None:
        life = Life(author.username)
        life_map[author.id] = life
    # 如果刚开始则返回欢迎词
    if not life.join_flag:
        join_str = life.join()
        await send_sample_msg(join_str, message)


async def get_current_life(author, message):
    life = life_map.get(author.id)
    if life is None:
        await send_sample_msg("你还没有加入游戏，请发送remake加入", message)
    else:
        return life


async def life_begin(author, message):
    life = await get_current_life(author, message)
    event = life.make_event()
    await send_sample_msg(event.post_result, message)


async def assign_properties(author, message):
    life: Life = await get_current_life(author, message)
    if life.init_flag:
        await send_sample_msg("您已经分配过初始值，不能再次分配", message)
    assign_str = get_cmd(message.content)
    value_list = assign_str.split("：")
    force = 0
    intel = 0
    money = 0
    result = ""
    for value in value_list[1:]:
        if "随机" in value:
            result = life.assign_properties_random(10)
            await send_sample_msg(result, message)
            return
        else:
            input_value_list = value.split("，")
            for input_value in input_value_list:
                if "f" in input_value:
                    force = int(input_value[1:])
                elif "m" in input_value:
                    intel = int(input_value[1:])
                elif "i" in input_value:
                    money = int(input_value[1:])

            result = life.assign_properties(force, intel, money)
    await send_sample_msg(result, message)


async def begin(author, message):
    life: Life = await get_current_life(author, message)
    result = life.make_event()
    await send_sample_msg(result, message)


async def _message_handler(event, message: qqbot.Message):
    """
    定义事件回调的处理

    :param event: 事件类型
    :param message: 事件对象（如监听消息是Message对象）
    """
    global cur_msg_api
    # 打印返回信息
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)
    cur_msg_api = qqbot.AsyncMessageAPI(t_token, False)
    content = get_cmd(message.content)
    if "remake" in content:
        await remake(message.author, message)
    elif "属性分配" in content:
        await assign_properties(message.author, message)
    elif "开始" in content:
        await begin(message.author, message)


if __name__ == "__main__":
    # async的异步接口的使用示例
    t_token = qqbot.Token(test_config["token"]["appid"], test_config["token"]["token"])
    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    qqbot.async_listen_events(t_token, False, qqbot_handler)
