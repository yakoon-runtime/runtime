from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from yakoon.base.models.key import Key


@dataclass
class AccountData:
    """
    Pure data object representing an account.

    This class contains only serializable account state.
    It has no persistence logic, no services, and no runtime behavior.

    The account is uniquely identified by its Key.
    """

    key: Key

    username: str | None = None
    password_hash: str | None = None

    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    is_disabled: bool = False
    last_login: datetime | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        """Returns True if the account has the given role."""
        return role in self.roles

    def is_active(self) -> bool:
        """Returns True if the account is not disabled."""
        return not self.is_disabled

    def to_dict(self) -> dict:
        """
        Serializes the account data into a plain dictionary.

        The Key is stored as its canonical string representation.
        Datetime values are converted to ISO 8601 strings.
        """
        return {
            "key": str(self.key),
            "username": self.username,
            "password_hash": self.password_hash,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "is_disabled": self.is_disabled,
            "last_login": (
                self.last_login.astimezone(UTC).isoformat()
                if self.last_login
                else None
            ),
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AccountData":
        """
        Creates an AccountData instance from a dictionary representation.
        """
        d = dict(d or {})

        raw_last_login = d.get("last_login")

        obj = cls(
            key=Key.from_str(d["key"]),
            username=d["username"],
            password_hash=d["password_hash"],
            roles=list(d.get("roles", [])),
            permissions=list(d.get("permissions", [])),
            is_disabled=d.get("is_disabled", False),
            data=dict(d.get("data", {})),
        )

        if raw_last_login:
            obj.last_login = datetime.fromisoformat(raw_last_login)

        return obj


class Account:
    """
    Lightweight façade around AccountData.

    This class exists purely for ergonomic access and grouping of
    account-related behavior. It does not handle persistence or policy.
    """

    def __init__(self, data: AccountData):
        self.data = data

    @property
    def key(self) -> Key:
        return self.data.key

    @property
    def username(self) -> str:
        return self.data.username

    @property
    def roles(self) -> list[str]:
        return self.data.roles

    @property
    def permissions(self) -> list[str]:
        return self.data.permissions

    @property
    def password_hash(self) -> str:
        return self.data.password_hash

    def has_role(self, role: str) -> bool:
        """Delegates to AccountData.has_role()."""
        return self.data.has_role(role)

    def is_active(self) -> bool:
        """Delegates to AccountData.is_active()."""
        return self.data.is_active()


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    account: Account | None = None
    reason: str | None = None
