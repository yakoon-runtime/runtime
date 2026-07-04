from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorldData:

    CURRENT_VERSION = 1

    name: str
    description: str = ""
    created_at: str = ""
    updated_at: str = ""

    _v: int = CURRENT_VERSION

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorldData:
        d = dict(d or {})
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            _v=d.get("_v", 0),
        )
