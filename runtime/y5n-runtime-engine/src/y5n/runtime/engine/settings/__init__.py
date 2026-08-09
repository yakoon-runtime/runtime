from dataclasses import dataclass, field

from y5n.runtime.store.event.settings import StorageSettings
from y5n.runtime.store.sequence.settings import SequenceSettings

from .base import BaseSettings
from .logging import LoggingSettings
from .runtime import RuntimeSettings


@dataclass
class Settings:
    base: BaseSettings = field(default_factory=BaseSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    sequencer: SequenceSettings = field(default_factory=SequenceSettings)
