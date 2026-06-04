from __future__ import annotations

from dataclasses import dataclass, field

from y5n.api.naming import Key, Namespace
from y5nstore.event import GetResult


@dataclass
class MembershipData:

    CURRENT_VERSION = 1

    user_key: Key
    group_key: Key

    enabled: bool = True

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return self.enabled

    def to_dict(self) -> dict:
        return {
            "user_key": str(self.user_key),
            "group_key": str(self.group_key),
            "enabled": self.enabled,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MembershipData:
        d = dict(d or {})

        return cls(
            user_key=Key.from_str(d["user_key"]),
            group_key=Key.from_str(d["group_key"]),
            enabled=d.get("enabled", True),
            _v=d.get("_v", 0),
        )


class Membership:
    def __init__(self, key: Key, data: MembershipData):
        self.key = key
        self.data = data

    @staticmethod
    def build_key(*, namespace: Namespace, user_key: Key, group_key: Key) -> Key:
        return Key(namespace=namespace, id=f"{group_key}:{user_key}")

    @property
    def user_key(self) -> Key:
        return self.data.user_key

    @property
    def group_key(self) -> Key:
        return self.data.group_key

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(cls, row: GetResult) -> Membership:
        data = row.require_object()
        return cls(
            key=row.key,
            data=MembershipData.from_dict(data),
        )
