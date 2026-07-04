from __future__ import annotations

from dataclasses import dataclass


@dataclass
class World:
    name: str
    description: str = ""
