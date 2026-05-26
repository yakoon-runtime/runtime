from dataclasses import dataclass, field

from y5nstore.event.settings import StorageSettings

from .ai import AISettings
from .base import BaseSettings
from .logging import LoggingSettings


@dataclass
class Settings:
    ai: AISettings = field(default_factory=AISettings)
    base: BaseSettings = field(default_factory=BaseSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
