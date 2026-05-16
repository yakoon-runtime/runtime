from __future__ import annotations

from .model import ManualEntry


class ManualService:

    def __init__(self):
        self._entries: dict[tuple[str, str], ManualEntry] = {}

    def register(
        self,
        scope: str,
        command: str,
        projection: str,
    ) -> None:

        self._entries[(scope, command)] = ManualEntry(
            command=command,
            scope=scope,
            projection=projection,
        )

    def get(
        self,
        scope: str,
        command: str,
    ) -> dict | None:

        result = self._entries.get((scope, command))
        if result:
            return {
                "command": result.command,
                "scope": result.scope,
                "projection": result.projection,
            }
        return None
