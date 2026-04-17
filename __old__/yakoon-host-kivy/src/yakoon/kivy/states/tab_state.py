from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TabRuntime:
    tab_id: str
    session: object
    host: object
    runner_thread: object


@dataclass
class TabState:
    counter: int = 0
    active_tab_id: str | None = None
    tabs: list[dict] = field(default_factory=list)
    pages: dict[str, object] = field(default_factory=dict)
    runtimes: dict[str, TabRuntime] = field(default_factory=dict)
