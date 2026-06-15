from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeConfig:
    name: str
    url: str
    autoconnect: bool = True


@dataclass
class YakoonConfig:
    runtimes: list[RuntimeConfig] = field(default_factory=list)
    theme: str | None = None
