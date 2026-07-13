from __future__ import annotations

from typing import Any

from typing_extensions import Protocol
from y5n.base.ports.protocols import OnSourceRead
from y5n.base.sources import (
    DataRequest,
    DataResult,
    DataSource,
)
from y5n.runtime.runtime.sessions import Session


class DiscoverySource(DataSource):

    def __init__(
        self,
        on_source: OnSourceRead,
        on_has_read_permission: OnHasReadPermission,
    ):
        self.on_source = on_source
        self.on_has_read_permission = on_has_read_permission

        self._selectors = {
            "runtime": self._runtime,
        }

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def read(
        self,
        request: DataRequest,
    ) -> DataResult:

        if not request.args():
            return DataResult.invalid(reason="empty query")

        matches = [k for k in self._selectors if request.has_option(k)]

        if not matches:
            return DataResult.invalid(reason="no selector")

        if len(matches) > 1:
            return DataResult.invalid(reason="multiple selectors")

        handler = self._selectors[matches[0]]

        return await handler(request)

    # ---------------------------------------------------------------------
    # Runtime Discovery
    # ---------------------------------------------------------------------

    async def _runtime(
        self,
        request: DataRequest,
    ) -> DataResult:

        app_id = request.context.get("app_id")
        session = request.context.get("session")
        mode = request.context.get("mode", "default")

        if not session:
            return DataResult.invalid(reason="missing session")

        # --------------------------------------------------
        # Load shell app
        # --------------------------------------------------

        result = await self.on_source(DataRequest("system:apps --shell"))

        if result.status != "ok":
            return result

        shell = result.one()

        shell_active = not app_id or app_id == shell["id"]
        if not app_id:
            app_id = shell["id"]

        # --------------------------------------------------
        # Runtime composition
        # --------------------------------------------------

        commands_by_key: dict[str, dict[str, Any]] = {}

        # -----------------
        # GLOBAL
        # -----------------

        result = await self.on_source(DataRequest("system:commands --global"))
        if result.status == "ok":
            for cmd in result.rows:
                self._include(commands_by_key, cmd, session=session, mode=mode)

        # -----------------
        # SHELL RUNTIME
        # -----------------

        if shell_active:
            result = await self.on_source(DataRequest("system:commands --shell"))
            if result.status == "ok":
                for cmd in result.rows:
                    self._include(commands_by_key, cmd, session=session, mode=mode)

        # -----------------
        # APP RUNTIME
        # -----------------

        result = await self.on_source(DataRequest(f"system:commands --by-app {app_id}"))
        if result.status == "ok":
            for cmd in result.rows:
                if cmd["scope"] in ("APP", "SHELL"):  #! own shell commands
                    self._include(commands_by_key, cmd, session=session, mode=mode)

        # --------------------------------------------------
        # Apps
        # --------------------------------------------------

        apps: list[dict[str, Any]] = []
        if shell_active:
            result = await self.on_source(DataRequest("system:apps --listed"))
            if result.status == "ok":
                apps = sorted(
                    [app for app in result.rows if app["id"] != shell["id"]],
                    key=lambda a: a["id"],
                )

        # --------------------------------------------------
        # Result
        # --------------------------------------------------

        commands = sorted(
            commands_by_key.values(),
            key=lambda c: c["key"],
        )

        return DataResult.ok(
            rows=[
                {
                    "mode": ("shell" if shell_active else "program"),
                    "commands": commands,
                    "apps": apps,
                }
            ]
        )

    # ---------------------------------------------------------------------
    # Runtime Filters
    # ---------------------------------------------------------------------

    def _include(
        self,
        target: dict[str, dict[str, Any]],
        cmd: dict[str, Any],
        *,
        session,
        mode: str,
    ):

        # -----------------
        # Permission
        # -----------------

        if not cmd["anonymous"]:
            perm_key = f"{cmd['app_id']}:{cmd['key']}"
            if not self.on_has_read_permission(session=session, perm_key=perm_key):
                return

        # -----------------
        # Visibility
        # -----------------

        allowed = self._allowed_visibilities(mode)
        if cmd["visibility"] not in allowed:
            return

        # -----------------
        # Merge
        # -----------------

        target.setdefault(
            cmd["key"],
            cmd,
        )

    def _allowed_visibilities(
        self,
        mode: str,
    ) -> set[str]:

        if mode == "default":
            return {"NORMAL"}

        if mode == "all":
            return {
                "NORMAL",
                "DEVELOPER",
            }

        if mode == "internal":
            return {
                "NORMAL",
                "DEVELOPER",
                "INTERNAL",
            }

        raise ValueError(f"invalid mode: {mode}")


# ----------------------------------
# PORTS
# ----------------------------------


class OnHasReadPermission(Protocol):

    def __call__(
        self,
        *,
        session: Session,
        perm_key: str,
    ) -> bool: ...
