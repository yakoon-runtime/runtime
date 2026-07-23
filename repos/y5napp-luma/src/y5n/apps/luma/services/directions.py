class Directions:
    PAIRS: dict[str, str] = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "up": "down",
        "down": "up",
        "in": "out",
        "out": "in",
    }

    @classmethod
    def opposite(cls, direction: str) -> str | None:
        return cls.PAIRS.get(direction.lower())

    @classmethod
    def is_known(cls, direction: str) -> bool:
        return direction.lower() in cls.PAIRS
