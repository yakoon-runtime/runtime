from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ErrorState:

    code: str
    data: dict[str, Any] | None = None

    @classmethod
    def with_data(cls, code: str, **data) -> ErrorState:

        return ErrorState(
            code=code,
            data=data,
        )
