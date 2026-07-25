from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from y5n.runtime.api.config import resolve_space_config
from y5n.runtime.store.event.settings import Backend, StorageSettings
from y5n.runtime.store.sequence.settings import SequenceSettings


def _backend(value: str | Any | None, default: Backend) -> Backend:
    if isinstance(value, str) and value in ("memory", "postgres"):
        return value
    return default


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)
    sequencer: SequenceSettings = field(default_factory=SequenceSettings)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> Settings:
        data = resolve_space_config("luma", config_dir)
        return cls(
            storage=StorageSettings(
                backend=_backend(
                    os.getenv("LUMA_STORE_BACKEND")
                    or data.get("storage", {}).get("backend"),
                    "memory",
                ),
                dsn=os.getenv("LUMA_STORE_DSN")
                or data.get("storage", {}).get("dsn")
                or "",
            ),
            sequencer=SequenceSettings(
                backend=_backend(
                    os.getenv("LUMA_SEQUENCER_BACKEND")
                    or data.get("sequencer", {}).get("backend"),
                    "memory",
                ),
                dsn=os.getenv("LUMA_SEQUENCER_DSN")
                or data.get("sequencer", {}).get("dsn")
                or "",
            ),
        )
