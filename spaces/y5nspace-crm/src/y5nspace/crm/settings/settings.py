from __future__ import annotations

from dataclasses import dataclass, field

from y5nstore.event import StorageSettings


@dataclass
class Settings:

    storage: StorageSettings = field(
        default_factory=lambda: StorageSettings(
            backend="duckdb",
            dsn="/var/lib/yakoon/spaces/crm.db",
        ),
    )
