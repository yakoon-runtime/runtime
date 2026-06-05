from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from .model import Permission


class PermissionSet(Protocol):
    """Minimal interface needed by spaces to build permission sets."""

    def add(self, perm: Permission) -> None: ...

    def merge(self, other: PermissionSet) -> None: ...

    def __iter__(self) -> Iterator[Permission]: ...
