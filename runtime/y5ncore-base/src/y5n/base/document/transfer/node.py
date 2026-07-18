"""Transport node — a plain dict.

Replaces the former Node dataclass.
"""

from __future__ import annotations

from typing import Any, TypedDict


class NodeData(TypedDict):
    id: str
    type: str
    parent: str | None
    depth: int
    props: dict[str, Any]
