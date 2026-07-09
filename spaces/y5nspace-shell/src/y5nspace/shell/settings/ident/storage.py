import os
from dataclasses import dataclass
from typing import Literal

Backend = Literal["memory", "postgres"]


@dataclass
class StorageSettings:
    backend: Backend = "memory"
    # backend: Backend = "postgres"

    dsn: str = os.getenv(
        "STORE_DSN",
        "postgresql://postgres:secret@localhost:5432/yakoon_dev",
    )
