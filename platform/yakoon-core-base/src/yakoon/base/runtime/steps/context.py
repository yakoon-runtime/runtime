from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from yakoon.base.runtime.commands import Request
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.runtime.sessions.session import Session

T = TypeVar("T")


@dataclass()
class StepContext:
    session: Session
    request: Request
    services: ServiceDirectory

    def get(self, key: type[T]) -> T:
        return self.services.get(key)
