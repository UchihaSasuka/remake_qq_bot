from .period import Period


class Player:
    def __init__(self, name, force_value=0, intel_value=0, money=0):
        self.id: int = 0
        self.age: int = 1
        self.name: str = name
        self.force_value: int = force_value
        self.intel_value: int = intel_value
        self.money: int = money
        self.period: Period = Period.BORN
        self.lucky: int = 0
