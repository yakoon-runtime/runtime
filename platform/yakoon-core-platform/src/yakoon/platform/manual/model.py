from dataclasses import dataclass


@dataclass(slots=True)
class ManualEntry:
    command: str
    scope: str
    projection: str
