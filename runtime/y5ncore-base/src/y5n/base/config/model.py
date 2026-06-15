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


@dataclass
class RuntimeFileConfig:
    listen: str = "ws://127.0.0.1:9100"
    spaces: list[str] = field(default_factory=list)
    known: dict[str, str] = field(default_factory=dict)
