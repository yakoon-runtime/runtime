import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BaseSettings:

    dev_mode = os.getenv("DEV_MODE", "false").lower() in ("1", "true", "yes")

    debug: bool = True
    """If True, enables verbose output and developer diagnostics."""

    config_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("YAKOON_CONFIG_DIR", "~/.config/yakoon")
        ).expanduser()
    )
