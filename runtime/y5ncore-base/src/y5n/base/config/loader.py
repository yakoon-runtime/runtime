from __future__ import annotations

from pathlib import Path

import yaml

from .model import ClientRuntime, RuntimeConfig, RuntimeFileConfig, ServerConfig, YakoonConfig

CONFIG_FILENAME = "yakoon.yml"
RUNTIME_FILENAME = "yakoon-runtime.yml"


def _search_paths(filename: str) -> list[Path]:
    cwd = Path.cwd()
    paths: list[Path] = []
    for parent in [cwd, *cwd.parents]:
        p = parent / filename
        paths.append(p)
        if p.exists():
            break
    paths.append(Path.home() / ".config" / "y5n" / filename)
    return paths


def load_config() -> tuple[YakoonConfig, Path | None]:
    for p in _search_paths(CONFIG_FILENAME):
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f)
            if not data:
                return YakoonConfig(), p

            runtimes = [
                RuntimeConfig(
                    name=r.get("name", r["url"]),
                    url=r["url"],
                    autoconnect=r.get("autoconnect", True),
                )
                for r in data.get("runtimes", [])
            ]

            server_raw = data.get("server")
            server = ServerConfig(**server_raw) if isinstance(server_raw, dict) else None
            runtime_raw = data.get("runtime")
            runtime_cfg = ClientRuntime(**runtime_raw) if isinstance(runtime_raw, dict) else None

            cfg = YakoonConfig(
                runtimes=runtimes,
                theme=data.get("theme"),
                server=server,
                runtime=runtime_cfg,
            )
            return cfg, p

    return YakoonConfig(), None


def load_runtime_config() -> tuple[RuntimeFileConfig, Path | None]:
    for p in _search_paths(RUNTIME_FILENAME):
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            return RuntimeFileConfig(
                listen=data.get("listen", "ws://127.0.0.1:9100"),
                spaces=data.get("spaces", []),
                known=data.get("known", {}),
            ), p
    return RuntimeFileConfig(), None


def save_config(cfg: YakoonConfig, path: Path) -> None:
    data = {}
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    data["runtimes"] = [
        {"name": r.name, "url": r.url, "autoconnect": r.autoconnect}
        for r in cfg.runtimes
    ]
    data["theme"] = cfg.theme

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
