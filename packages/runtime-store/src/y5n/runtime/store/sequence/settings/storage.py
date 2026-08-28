from dataclasses import dataclass
from typing import Literal

Backend = Literal["memory", "postgres"]


@dataclass
class SequenceSettings:
    # ``dsn`` is required — the store carries no default connection string.
    dsn: str
    backend: Backend = "memory"
