from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from y5n.base.config import resolve_space_config
from y5nstore.event.settings import StorageSettings


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> Settings:
        data = resolve_space_config("crm", config_dir)
        storage_data = data.get("storage", {})
        defaults = StorageSettings()

        return cls(
            storage=StorageSettings(
                backend=os.getenv("CRM_STORE_BACKEND")
                    or storage_data.get("backend")
                    or defaults.backend,
                dsn=os.getenv("CRM_STORE_DSN")
                    or storage_data.get("dsn")
                    or defaults.dsn,
            )
        )
