from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from y5n.runtime.api.naming import Key
from y5n.runtime.store.event import GetResult


@dataclass
class AccountData:

    CURRENT_VERSION = 1

    name: str
    enabled: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return self.enabled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "_v": self._v,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, d: dict) -> AccountData:
        d = dict(d or {})

        return cls(
            name=d["name"],
            enabled=d.get("enabled", True),
            data=dict(d.get("data", {})),
            _v=d.get("_v", 0),
        )


class Account:

    def __init__(self, key: Key, data: AccountData):
        self.key = key
        self.data = data

    @property
    def name(self) -> str:
        return self.data.name

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(cls, row: GetResult) -> Account:
        data = row.require_object()
        return cls(
            key=row.key,
            data=AccountData.from_dict(data),
        )
