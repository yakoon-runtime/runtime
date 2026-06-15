from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeConfig:
    name: str
    url: str
    autoconnect: bool = True


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass
class ClientRuntime:
    url: str = "ws://localhost:9100"


@dataclass
class YakoonConfig:
    runtimes: list[RuntimeConfig] = field(default_factory=list)
    theme: str | None = None
    server: ServerConfig | None = None
    runtime: ClientRuntime | None = None


@dataclass
class RuntimeFileConfig:
    listen: str = "ws://127.0.0.1:9100"
    spaces: list[str] = field(default_factory=list)
    known: dict[str, str] = field(default_factory=dict)
