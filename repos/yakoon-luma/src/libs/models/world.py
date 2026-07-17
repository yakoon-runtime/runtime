from dataclasses import dataclass


@dataclass
class World:
    id: str
    name: str
    description: str = ""
    entry_box_id: str | None = None
