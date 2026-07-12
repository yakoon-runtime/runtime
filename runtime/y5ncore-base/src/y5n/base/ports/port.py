from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T", bound="Callable")


@dataclass(frozen=True)
class Port(Generic[T]):
    """A named capability identifier for the runtime.

    A Port decouples the identity of a capability (its name)
    from its type signature (the protocol).  Two modules that
    share the same Port object can provide and retrieve a
    capability without sharing Python class identity.
    """

    name: str
    """Unique capability name across the platform."""

    protocol: type[T] | None = None
    """Optional type signature for static type checking."""

    def __repr__(self) -> str:
        return f"Port({self.name!r})"
