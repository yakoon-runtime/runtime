from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yakoon.base.runtime.session.session import Session


@dataclass
class TabState:
    tabs: list[dict] = field(default_factory=list)  # [{"id": str, "title": str}, ...]
    pages: dict[str, Any] = field(default_factory=dict)  # tab_id -> page/widget
    runtimes: dict[str, TabRuntime] = field(default_factory=dict)
    active_tab_id: str | None = None
    counter: int = 0


@dataclass
class TabRuntime:
    tab_id: str
    session: Session
