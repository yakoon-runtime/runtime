from dataclasses import dataclass, field

from y5nstore.event.settings import StorageSettings


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)
