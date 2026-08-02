"""Resource — the content unit delivered by a resolve capability.

A resolve capability (``man``, ``projection``, ...) returns a ``Resource``.
The public contract is exactly two methods: ``read_text()`` and
``read_bytes()``. The carrier behind a Resource is an implementation detail.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path


@dataclass(frozen=True)
class Resource:
    """A readable content unit produced by a resolve capability."""

    _read_text: Callable[[], str]
    _read_bytes: Callable[[], bytes]

    @classmethod
    def text(cls, content: str) -> Resource:
        """Wrap a literal string."""
        return cls(lambda: content, lambda: content.encode())

    @classmethod
    def path(cls, path: Path) -> Resource:
        """Wrap a filesystem path."""
        return cls(path.read_text, path.read_bytes)

    @classmethod
    def traversable(cls, trav: Traversable) -> Resource:
        """Wrap a package resource (``importlib.resources.files(...)``)."""
        return cls(trav.read_text, trav.read_bytes)

    def read_text(self) -> str:
        return self._read_text()

    def read_bytes(self) -> bytes:
        return self._read_bytes()


__all__ = ["Resource"]
