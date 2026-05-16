from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yakoon.platform.runtime import UnhandledError


@dataclass
class ErrorState:

    key: str
    data: dict[str, Any] | None = None

    @classmethod
    def by_key(cls, *, key: str, **data) -> ErrorState:

        return ErrorState(
            key=key,
            data=data,
        )

    @classmethod
    def by_type(cls, *, type_key: type[Exception], **data) -> ErrorState:

        return ErrorState(
            key=str(type(type_key())),
            data=data,
        )

    @classmethod
    def extract_state(cls, error: Exception) -> ErrorState:
        if error.args:
            first = error.args[0]
            if isinstance(first, ErrorState):
                return first

        return ErrorState.by_type(type_key=UnhandledError)
