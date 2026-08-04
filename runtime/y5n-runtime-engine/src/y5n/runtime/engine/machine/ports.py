"""Shared protocol definitions for the machine package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from y5n.runtime.engine.runtime import Session

if TYPE_CHECKING:
    from .runner import Runner


class OnCreateRunner(Protocol):
    def __call__(self, *, session) -> Runner: ...


class OnAuditWarning(Protocol):
    def __call__(self, *, message: str, session: Session) -> None: ...


class OnSuggest(Protocol):
    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...
