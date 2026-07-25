from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Any

from .context import InputContext


class Routing(Enum):
    DEFAULT = auto()
    BYPASS_FLOW = auto()


@dataclass(frozen=True, slots=True)
class Event:
    payload: Any
    context: InputContext | None = None
    routing: Routing = Routing.DEFAULT

    @classmethod
    def from_raw(cls, data: str, context=None, *, routing: Routing = Routing.DEFAULT):
        return cls(payload=data, context=context, routing=routing)

    def update(
        self,
        *,
        payload: Any | None = None,
    ) -> Event:

        return replace(
            self,
            payload=payload if payload is not None else self.payload,
        )
