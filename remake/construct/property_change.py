class PropertyChange:
    def __init__(self, change_map):
        self.force: int = change_map["force"] if change_map.get("force") is not None else 0
        self.intel: int = change_map["intel"] if change_map.get("intel") is not None else 0
        self.money: int = change_map["money"] if change_map.get("money") is not None else 0
        self.lucky: int = change_map["lucky"] if change_map.get("lucky") is not None else 0
