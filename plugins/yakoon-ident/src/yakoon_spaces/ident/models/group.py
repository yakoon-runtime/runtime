from __future__ import annotations

from dataclasses import dataclass, field

from yakoon.base.naming import Key
from yakoon.storage.eventstore import GetResult


@dataclass
class GroupData:

    CURRENT_VERSION = 1

    name: str
    enabled: bool = True

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return self.enabled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GroupData:
        d = dict(d or {})
        obj = cls(
            name=d["name"],
            enabled=d.get("enabled", True),
            _v=d.get("_v", 0),
        )

        return obj


class Group:
    def __init__(self, key: Key, data: GroupData):
        self.key = key
        self.data = data

    @property
    def name(self) -> str:
        return self.data.name

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(cls, row: GetResult) -> Group:
        data = row.require_object()
        return cls(
            key=row.key,
            data=GroupData.from_dict(data),
        )
