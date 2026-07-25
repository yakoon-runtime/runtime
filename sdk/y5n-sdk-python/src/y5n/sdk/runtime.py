"""Runtime — backward-compatible facade for all domain modules.

Prefer importing domain modules directly:

    from y5n.sdk import fs, io, timer, scheduler, network, viewport
"""

from __future__ import annotations

from .fs import fs
from .io import io
from .network import network
from .scheduler import scheduler
from .session import session
from .timer import timer
from .viewport import viewport

__all__ = [
    "fs",
    "io",
    "network",
    "scheduler",
    "session",
    "timer",
    "viewport",
]
