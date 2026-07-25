"""Session — identity and preferences of the current user.

Built from the ``session`` and ``user`` dicts in Context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Session:
    key: str = ""
    locale: str = ""
    user: str | None = None
    user_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_context(
        cls, session_dict: dict[str, Any], user_dict: dict[str, Any]
    ) -> Session:
        return cls(
            key=session_dict.get("key", ""),
            locale=session_dict.get("lang", ""),
            user=user_dict.get("name") or user_dict.get("id"),
            user_id=user_dict.get("id"),
            data=session_dict.get("data", {}),
        )
