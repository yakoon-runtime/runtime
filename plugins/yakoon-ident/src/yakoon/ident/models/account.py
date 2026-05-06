from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yakoon.base.naming import Key
from yakoon.storage.eventstore import GetResult


@dataclass
class AccountData:

    CURRENT_VERSION = 1

    name: str
    is_disabled: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return not self.is_disabled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_disabled": self.is_disabled,
            "_v": self._v,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, d: dict) -> AccountData:
        d = dict(d or {})

        return cls(
            name=d["name"],
            is_disabled=d.get("is_disabled", False),
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
    def from_row(cls, key: Key, row: GetResult) -> Account:
        data = row.require_object()
        return cls(
            key=key,
            data=AccountData.from_dict(data),
        )
