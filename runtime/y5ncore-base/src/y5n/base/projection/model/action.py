from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Action:
    id: str | None = None
    label: str = ""
    command: str | None = None
    scope: str | None = None
