import json
import random
from pathlib import Path
from typing import Dict

from construct.event import Event
from construct.period import Period
from construct.player import Player
from construct.property_change import PropertyChange

resource_path = Path(__file__).parent / "resources"

player_property = {
    "force": "武力值",
    "intel": "智力值",
    "money": "财力值",
}


def init_event():
    path = resource_path / "event2.json"
    data: Dict[str, dict] = json.load(path.open("r", encoding="utf8"))
    event = Event()
    event.name = data["name"]
    event.desc = data["desc"]
    triggers = data["trigger"]
    trigger_str = ""
    event_map = {}

    # 设置属性变化 以及提示语言
    change_map = {}
    for trigger_key in triggers.keys():
        symbol = ""
        if triggers[trigger_key] > 0:
            symbol = "+"
        trigger_str += "%s%s%s，" % (player_property[trigger_key], symbol, triggers[trigger_key])
        change_map[trigger_key] = triggers[trigger_key]
    trigger_str = trigger_str[0:-1]
    event.post_result = "%s因此，%s" % (event.desc, trigger_str)
    event.change = PropertyChange(change_map)

    # 按时期维度增添到事件列表
    period = Period(data["period"])
    event.period = period

    if event_map is None:
        event_map = {}

    event_list = event_map.get(period)
    if event_list is None:
        event_list = [event]
    event_map[period] = event_list
    return event_map


global_event_map = init_event()


class Life:
    def __init__(self, author):
        self.player = Player(author)
        self.join_flag = False
        self.init_flag = False

    def join(self):
        self.join_flag = False
        return "你好%s:欢迎加入三国人生，游戏开始前请分配10点基础属性：武力值（f）,智力值（i）,财力值（m），如：属性分配：f3,i4,m3,也可以输入属性分配：随机，由系统随机分配。" % self.player.name

    def make_event(self):
        event: Event = random.choice(global_event_map[self.player.period])
        return event.post_result % self.player.name

    def assign_properties(self, force=3, intel=3, money=4):
        if force + intel + money != 10:
            return "属性分配失败：三个属性分配值之和必须为10"
        self.player.force_value = force
        self.player.intel_value = intel
        self.player.money = money
        return "属性分配成功，武力值：%s，智力值：%s，财力值：%s，请发送“开始”开始你的精彩人生吧" % (force, intel, money)

    def assign_properties_random(self, total_value):
        first = random.randint(1, total_value - 2)
        second = random.randint(1, total_value - first - 1)
        third = total_value - first - second
        return self.assign_properties(first, second, third)
