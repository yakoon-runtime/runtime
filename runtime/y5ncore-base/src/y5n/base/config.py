from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def resolve_space_config(
    space_id: str, config_dir: Path | None = None
) -> dict[str, Any]:
    search_dirs: list[Path] = []

    if config_dir:
        search_dirs.append(config_dir)

    env_dir = os.getenv("YAKOON_CONFIG_DIR")
    if env_dir:
        search_dirs.append(Path(env_dir).expanduser())

    search_dirs.append(Path("~/.config/yakoon").expanduser())

    for base in search_dirs:
        path = base / "spaces" / f"{space_id}.yml"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data or {}

    return {}
