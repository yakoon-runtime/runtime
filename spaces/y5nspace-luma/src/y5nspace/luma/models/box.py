from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Box:
    id: str
    world_id: str
    parent_id: str | None = None
    name: str = ""
    description: str = ""
    portable: bool = False
