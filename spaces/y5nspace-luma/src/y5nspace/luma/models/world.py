from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorldData:
    CURRENT_VERSION = 1
    name: str
    description: str = ""
    entry_box_id: str | None = None
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "entry_box_id": self.entry_box_id,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorldData:
        d = dict(d or {})
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            entry_box_id=d.get("entry_box_id"),
            _v=d.get("_v", 0),
        )
