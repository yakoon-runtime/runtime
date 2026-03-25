from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from yakoon.base.runtime.commands import Request
    from yakoon.base.runtime.services import ServiceDirectory
    from yakoon.base.runtime.sessions import Session

T = TypeVar("T")


@dataclass()
class StepContext:
    session: Session
    request: Request
    services: ServiceDirectory

    def get(self, key: type[T]) -> T:
        return self.services.get(key)
