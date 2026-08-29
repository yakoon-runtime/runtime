from dataclasses import dataclass, field

from .logging import LoggingSettings
from .runtime import RuntimeSettings


@dataclass
class Settings:
    """Runtime settings.

    Storage is not configured here (ADR-19): every physical store is
    materialized from the installation by its StoreFactory. The runtime
    holds no storage settings.
    """

    logging: LoggingSettings = field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
