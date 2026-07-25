from dataclasses import dataclass, field

from y5n.runtime.store.event.settings import StorageSettings


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)
