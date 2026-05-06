from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from yakoon.base.naming import Key
from yakoon.storage.eventstore import GetResult


@dataclass
class UserData:

    CURRENT_VERSION = 1

    username: str
    password_hash: str | None = None
    is_disabled: bool = False
    last_login: datetime | None = None
    data: dict[str, Any] = field(default_factory=dict)

    _v: int = field(default=CURRENT_VERSION)

    def is_active(self) -> bool:
        return not self.is_disabled

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "is_disabled": self.is_disabled,
            "last_login": (
                self.last_login.astimezone(UTC).isoformat() if self.last_login else None
            ),
            "data": dict(self.data),
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> UserData:
        d = dict(d or {})

        raw_last_login = d.get("last_login")

        obj = cls(
            username=d["username"],
            password_hash=d["password_hash"],
            is_disabled=d.get("is_disabled", False),
            data=dict(d.get("data", {})),
            _v=d.get("_v", 0),
        )

        if raw_last_login:
            obj.last_login = datetime.fromisoformat(raw_last_login)

        return obj


class User:
    def __init__(self, key: Key, data: UserData):
        self.key = key
        self.data = data

    @property
    def username(self) -> str:
        return self.data.username

    def is_active(self) -> bool:
        return self.data.is_active()

    @classmethod
    def from_row(cls, key: Key, row: GetResult) -> User:
        data = row.require_object()
        return cls(
            key=key,
            data=UserData.from_dict(data),
        )
