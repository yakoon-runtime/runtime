from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yakoon.base.naming import Key
from yakoon.storage.eventstore import GetResult


@dataclass
class MembershipData:
    key: Key

    user_id: Key
    account_id: Key

    roles: list[str] = field(default_factory=list)

    is_disabled: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def is_active(self) -> bool:
        return not self.is_disabled

    def to_dict(self) -> dict:
        return {
            "key": str(self.key),
            "user_id": str(self.user_id),
            "account_id": str(self.account_id),
            "roles": list(self.roles),
            "is_disabled": self.is_disabled,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, d: dict) -> MembershipData:
        d = dict(d or {})

        return cls(
            key=Key.from_str(d["key"]),
            user_id=Key.from_str(d["user_id"]),
            account_id=Key.from_str(d["account_id"]),
            roles=list(d.get("roles", [])),
            is_disabled=d.get("is_disabled", False),
            data=dict(d.get("data", {})),
        )


class Membership:
    def __init__(self, data: MembershipData):
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
        return cls(MembershipData.from_dict(data))
