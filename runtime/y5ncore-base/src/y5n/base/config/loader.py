from __future__ import annotations

from pathlib import Path

import yaml

from .model import RuntimeConfig, YakoonConfig

CONFIG_FILENAME = "yakoon.yml"

CONFIG_SEARCH_PATHS: list[Path] = [
    Path.cwd() / CONFIG_FILENAME,
    Path("~/.config/y5n") / CONFIG_FILENAME,
]


def load_config() -> tuple[YakoonConfig, Path | None]:
    for p in CONFIG_SEARCH_PATHS:
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

            cfg = YakoonConfig(
                runtimes=runtimes,
                theme=data.get("theme"),
            )
            return cfg, p

    return YakoonConfig(), None


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
