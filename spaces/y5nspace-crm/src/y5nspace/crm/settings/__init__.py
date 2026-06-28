from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from y5n.base.config import resolve_space_config
from y5nstore.event.settings import Backend, StorageSettings
from y5nstore.sequence.settings import SequenceSettings


def _backend(value: str | Any | None, default: Backend) -> Backend:
    if isinstance(value, str) and value in ("memory", "postgres"):
        return value  # type: ignore[return-value]
    return default


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)
    sequencer: SequenceSettings = field(default_factory=SequenceSettings)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> Settings:
        data = resolve_space_config("crm", config_dir)
        storage_data = data.get("storage", {})
        sequencer_data = data.get("sequencer", {})

        return cls(
            storage=StorageSettings(
                backend=_backend(
                    os.getenv("CRM_STORE_BACKEND")
                    or storage_data.get("backend"),
                    "memory",
                ),
                dsn=os.getenv("CRM_STORE_DSN")
                    or storage_data.get("dsn")
                    or "",
            ),
            sequencer=SequenceSettings(
                backend=_backend(
                    os.getenv("CRM_SEQUENCER_BACKEND")
                    or sequencer_data.get("backend"),
                    "memory",
                ),
                dsn=os.getenv("CRM_SEQUENCER_DSN")
                    or sequencer_data.get("dsn")
                    or "",
            ),
        )
