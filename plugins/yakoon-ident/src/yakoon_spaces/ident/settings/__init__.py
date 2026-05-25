from dataclasses import dataclass, field

from yakoon.storage.settings import StorageSettings


@dataclass
class Settings:
    storage: StorageSettings = field(default_factory=StorageSettings)
