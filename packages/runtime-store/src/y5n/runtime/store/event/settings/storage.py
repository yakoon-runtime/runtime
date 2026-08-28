from dataclasses import dataclass
from typing import Literal

Backend = Literal["memory", "postgres"]


@dataclass
class StorageSettings:
    # ``dsn`` is required — the store carries no default connection string.
    dsn: str
    backend: Backend = "memory"
