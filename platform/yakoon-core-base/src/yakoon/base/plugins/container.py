from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

# ----------------------------------
# MODULE PORTS
# ----------------------------------

T = TypeVar("T")


@dataclass(frozen=True)
class ModulePorts:
    on_register: OnRegister
    on_get_port: OnGetPort


# ----------------------------------
# PORTS
# ----------------------------------


class OnRegister(Protocol):
    def __call__(self, port: object, capability: object) -> None: ...


class OnGetPort(Protocol):
    def __call__(self, port: type[T]) -> T: ...
