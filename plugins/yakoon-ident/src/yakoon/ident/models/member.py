from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yakoon.base.naming import Key
from yakoon.storage.eventstore import GetResult


@dataclass
class MembershipData:

    CURRENT_VERSION = 1

    user_id: Key
    account_id: Key

    roles: list[str] = field(default_factory=list)
    enabled: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    _v: int = field(default=CURRENT_VERSION)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def is_active(self) -> bool:
        return self.enabled

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "account_id": str(self.account_id),
            "roles": list(self.roles),
            "enabled": self.enabled,
            "data": dict(self.data),
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MembershipData:
        d = dict(d or {})

        return cls(
            user_id=Key.from_str(d["user_id"]),
            account_id=Key.from_str(d["account_id"]),
            roles=list(d.get("roles", [])),
            enabled=d.get("enabled", True),
            data=dict(d.get("data", {})),
            _v=d.get("_v", 0),
        )


class Membership:
    def __init__(self, key: Key, data: MembershipData):
        self.key = key
        self.data = data

    @property
    def user_id(self) -> Key:
        return self.data.user_id

    @property
    def account_id(self) -> Key:
        return self.data.account_id

    @property
    def roles(self) -> list[str]:
        return self.data.roles

    def has_role(self, role: str) -> bool:
        return self.data.has_role(role)

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(cls, row: GetResult) -> Membership:
        data = row.require_object()
        return cls(
            key=row.key,
            data=MembershipData.from_dict(data),
        )
