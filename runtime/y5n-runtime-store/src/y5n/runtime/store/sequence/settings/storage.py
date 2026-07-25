import os
from dataclasses import dataclass
from typing import Literal

Backend = Literal["memory", "postgres"]


@dataclass
class SequenceSettings:
    backend: Backend = "memory"

    dsn: str = os.getenv(
        "SEQUENCE_STORE_DSN",
        "postgresql://postgres:secret@localhost:5432/yakoon_sequence",
    )
