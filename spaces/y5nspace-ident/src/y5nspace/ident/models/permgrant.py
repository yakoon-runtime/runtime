from __future__ import annotations

from dataclasses import dataclass, field

from y5n.base.naming import Key, Namespace
from y5nstore.event import GetResult


@dataclass
class PermissionGrantData:

    CURRENT_VERSION = 1

    subject_key: Key
    permission_key: str

    bits: str = "x"
    deny: bool = False
    enabled: bool = True

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return self.enabled

    def to_dict(self) -> dict:
        return {
            "subject_key": str(self.subject_key),
            "permission_key": self.permission_key,
            "bits": self.bits,
            "deny": self.deny,
            "enabled": self.enabled,
            "_v": self._v,
        }

    @classmethod
    def from_dict(
        cls,
        d: dict,
    ) -> PermissionGrantData:

        d = dict(d or {})

        return cls(
            subject_key=Key.from_str(d["subject_key"]),
            permission_key=d["permission_key"],
            bits=d.get("bits", "x"),
            deny=d.get("deny", False),
            enabled=d.get("enabled", True),
            _v=d.get("_v", 0),
        )


class PermissionGrant:

    def __init__(
        self,
        key: Key,
        data: PermissionGrantData,
    ):
        self.key = key
        self.data = data

    @staticmethod
    def build_key(
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
    ) -> Key:

        return Key(
            namespace=namespace,
            id=f"{subject_key}:{permission_key}",
        )

    @property
    def subject_key(self) -> Key:
        return self.data.subject_key

    @property
    def permission_key(self) -> str:
        return self.data.permission_key

    @property
    def bits(self) -> str:
        return self.data.bits

    @property
    def deny(self) -> bool:
        return self.data.deny

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(
        cls,
        row: GetResult,
    ) -> PermissionGrant:

        data = row.require_object()

        return cls(
            key=row.key,
            data=PermissionGrantData.from_dict(data),
        )
