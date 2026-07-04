from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Exit:
    id: str
    world_id: str
    source_box_id: str
    target_box_id: str
    name: str = ""
    description: str = ""
    direction: str = ""
