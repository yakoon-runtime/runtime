from dataclasses import dataclass, field

from .base import BaseSettings
from .logging import LoggingSettings
from .runtime import RuntimeSettings


@dataclass
class Settings:
    """Runtime settings.

    Storage is not configured here (ADR-19): every physical store is
    materialized from the installation by its StoreFactory. The runtime
    holds no storage settings.
    """

    base: BaseSettings = field(default_factory=BaseSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
