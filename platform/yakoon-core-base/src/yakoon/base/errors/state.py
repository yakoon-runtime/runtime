from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yakoon.platform.runtime import UnhandledError

ErrorKey = str | type[Exception]


@dataclass
class ErrorState:

    key: ErrorKey
    data: dict[str, Any] | None = None

    @classmethod
    def by_key(cls, *, key: str, **data) -> ErrorState:

        return ErrorState(
            key=key,
            data=data,
        )

    @classmethod
    def by_type(cls, *, key: type[Exception], **data) -> ErrorState:

        return ErrorState(
            key=key,
            data=data,
        )

    @classmethod
    def extract_state(cls, error: Exception) -> ErrorState:
        if error.args:
            first = error.args[0]
            if isinstance(first, ErrorState):
                return first

        return ErrorState.by_type(key=UnhandledError)
