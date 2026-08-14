from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any

from y5n.runtime.api.tokens import TokenQuery


@dataclass(frozen=True)
class DataRequest:

    query: str
    context: dict[str, Any] = field(default_factory=dict)

    _source: str = field(init=False, repr=False)
    _query: TokenQuery = field(init=False, repr=False)

    def __post_init__(self) -> None:
        parts = shlex.split(self.query)

        if not parts:
            raise ValueError("Empty data request")

        object.__setattr__(self, "_source", parts[0])
        object.__setattr__(self, "_query", TokenQuery(parts[1:]))

    @property
    def source(self) -> str:
        return self._source

    def args(self) -> list[str]:
        return self._query.args()

    def token(self, index: int, default: Any = None) -> Any:
        return self._query.token(index, default)

    def arg(self, index: int, default: Any = None) -> Any:
        return self._query.arg(index, default)

    def has_args(self) -> bool:
        return self._query.has_args()

    def arg_count(self) -> int:
        return self._query.arg_count()

    def has_option(self, name: str) -> bool:
        return self._query.has_option(name)

    def option(self, name: str, default: Any = None) -> Any:
        return self._query.option(name, default)
