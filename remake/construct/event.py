from .period import Period
from .event_type import EventType
from .trigger import Trigger
from .property_change import PropertyChange


class Event:
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.desc: str = ""
        self.options: list = []
        self.post_result: str = ""
        self.period: Period = None
        self.type: EventType = EventType.ORDINARY
        self.trigger: Trigger = None
        self.change: PropertyChange = None
