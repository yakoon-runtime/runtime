from dataclasses import dataclass, field

from y5n.runtime.store.event.settings import StorageSettings

from .ai import AISettings
from .base import BaseSettings
from .logging import LoggingSettings
from .runtime import RuntimeSettings


@dataclass
class Settings:
    ai: AISettings = field(default_factory=AISettings)
    base: BaseSettings = field(default_factory=BaseSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
