from typing import Any

from yakoon.base.commands import CommandKind
from yakoon.base.sources import DataRequest, OnDataSource


class CommandManService:

    def __init__(
        self,
        on_source: OnDataSource,
        on_has_permission,
    ):
        self.on_source = on_source
        self.on_has_permission = on_has_permission

    async def get_entries(
        self,
        *,
        app_id: str,
        session,
        mode: str,
        kind: CommandKind | None,
    ) -> list[dict[str, Any]]:

        # ----------------------------------
        # 1. Load commands
        # ----------------------------------
        result = await self.on_source(DataRequest(f"system:commands --by-app {app_id}"))

        if result.status != "ok":
            return []

        rows = result.rows

        # ----------------------------------
        # 2. Permission filter
        # ----------------------------------
        on_has_permission = self.on_has_permission
        rows = [
            r
            for r in rows
            if r["anonymous"]
            or on_has_permission(
                session=session,
                perm_key=f"{r['app_id']}:{r['key']}",
            )
        ]

        # ----------------------------------
        # 3. Visibility filter
        # ----------------------------------
        allowed = self._allowed_visibilities(mode)

        rows = [r for r in rows if r["visibility"] in allowed]

        # ----------------------------------
        # 4. Kind filter
        # ----------------------------------
        if kind:
            rows = [r for r in rows if r["kind"] == kind.name]

        # ----------------------------------
        # 5. Sort (stabil!)
        # ----------------------------------
        rows.sort(key=lambda r: r["key"])

        return rows

    def _allowed_visibilities(self, mode: str) -> set[str]:

        if mode == "default":
            return {"NORMAL"}

        if mode == "all":
            return {"NORMAL", "DEVELOPER"}

        if mode == "internal":
            return {"NORMAL", "DEVELOPER", "INTERNAL"}

        raise ValueError(f"invalid mode: {mode}")
