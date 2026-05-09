from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from yakoon.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    Request,
)
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.projection import Projection
from yakoon.base.sources import DataRequest, OnDataSource


class CmdMan(Command):

    key = "man"
    scope = CommandScope.GLOBAL
    anonymous = True

    def __init__(
        self,
        on_source: OnDataSource,
        on_project: OnProjectCmd,
        on_list_manual: OnListManual,
        on_project_manual: OnProjectManual,
        on_get_active_app: OnGetActiveApp,
        # on_list_commands_for_app: OnListCommandsForApp,
        # on_get_commands_for_manual: OnListCommandsForManual,
    ):
        self.on_source = on_source
        self.on_project = on_project
        self.on_list_manual = on_list_manual
        self.on_project_manual = on_project_manual
        self.on_get_active_app = on_get_active_app
        # self.on_list_commands_for_app = on_list_commands_for_app
        # self.on_get_commands_for_manual = on_get_commands_for_manual

    async def run(self, request: Request):

        args = request.arg(0)
        if not args:
            yield self.show_index(request)
        else:
            yield self.show_manual(request)

    async def show_manual(self, request: Request):

        command_key = request.arg(0)
        if not command_key:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": "",
                },
            )
            yield out(projection)
            return

        # privileged access: controller management

        active_app_id = self.on_get_active_app()
        if not active_app_id:
            data = await self.on_source(DataRequest("system:apps --shell"))

            shell = data.one()
            active_app_id = shell["id"]

        # active controller must be listed to show man pages
        data = await self.on_source(DataRequest(f"system:apps --by-id {active_app_id}"))
        if not any(a["is_listed"] for a in data.rows):
            return

        # ----------------------------------------------------
        # 1) Try active app first
        # ----------------------------------------------------
        owner_app_id = active_app_id
        result = await self.on_source(
            DataRequest(f"system:commands --by-app {owner_app_id}")
        )

        # ----------------------------------------------------
        # 2) If not found: try GLOBAL commands from all apps
        # ----------------------------------------------------
        command: dict | None = None
        command = next((c for c in result.rows if c["key"] == command_key), None)
        if not command:
            global_hits: list[tuple[str, dict]] = []

            data = await self.on_source(DataRequest("system:apps --all"))

            for app in [a for a in data.rows if a["is_listed"]]:
                result = await self.on_source(
                    DataRequest(f"system:commands --by-app {app['id']}")
                )

                for c in result.rows:
                    if c["key"] == command_key and c["scope"] == "GLOBAL":
                        global_hits.append((app["id"], c))

            if len(global_hits) == 1:
                owner_app_id, command = global_hits[0]
            elif len(global_hits) > 1:
                raise RuntimeError(
                    f"Duplicate GLOBAL command key detected: {command_key}"
                )

        # ----------------------------------------------------
        # 3) Render or show "no entry"
        # ----------------------------------------------------
        if not command:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )
            yield out(projection)
            return

        # controller has to exist - command was found before.
        data = await self.on_source(DataRequest(f"system:apps --by-id {owner_app_id}"))
        app = data.one()
        if not app:
            raise RuntimeError("Controller not found")

        controller_id = command["controller_id"]

        try:

            resources = app["resources"][controller_id]
            projection = await self.on_project_manual(
                resources=resources,
                name="details.sam",
                state={
                    "command_key": command_key,
                },
            )
            yield out(projection)

        except LookupError:
            # use the own projector.
            projection = await self.on_project(
                name="error.sam",
                state={"command_key": command_key},
            )
            yield out(projection)

    async def show_index(self, request: Request):

        data = await self.on_source(DataRequest("system:apps --shell"))

        shell = data.one()
        active_app_id = self.on_get_active_app()
        mode = self.resolve_man_mode(request)

        globals_by_key: dict[str, dict] = {}

        # ----------------------------
        # Shell mode (no active or shell)
        # ----------------------------
        if not active_app_id or active_app_id == shell["id"]:
            # 1) shell commands (defined in shell controller)
            shell_commands = await self.on_list_manual(app_id=shell["id"], mode=mode)

            # 2) global commands (defined anywhere)
            data = await self.on_source(DataRequest("system:apps --all"))
            for app in [a for a in data.rows if bool(a["is_listed"])]:
                for cmd in await self.on_list_manual(app_id=app["id"], mode=mode):
                    if cmd["scope"] == "GLOBAL":
                        globals_by_key[cmd["key"]] = cmd

            # merge, avoid duplicates
            merged_by_key: dict[str, dict] = {c["key"]: c for c in shell_commands}
            for k, v in globals_by_key.items():
                merged_by_key.setdefault(k, v)

            shell_commands = sorted(merged_by_key.values(), key=lambda c: c["key"])

            data = await self.on_source(DataRequest("system:apps --listed"))
            apps = sorted(
                [c for c in data.rows if c["id"] != shell["id"]],
                key=lambda c: c["id"],
            )

            projection = await self.on_project(
                name="overview.sam",
                state={
                    "mode": "shell",
                    "shell_commands": shell_commands,
                    "apps": apps,
                },
            )
            yield out(projection)
            return

        # ----------------------------
        # Program mode (active != shell)
        # ----------------------------

        # 1) Collect GLOBAL commands from all app (system-wide available)
        data = await self.on_source(DataRequest("system:apps --all"))
        for app in data.rows:
            for cmd in await self.on_list_manual(app_id=app["id"], mode=mode):
                if cmd["scope"] == "GLOBAL":
                    globals_by_key[cmd["key"]] = cmd

        # 2) Collect commands from active app that are executable in program mode
        program_by_key: dict[str, dict] = {}
        for cmd in await self.on_list_manual(app_id=active_app_id, mode=mode):
            if cmd["scope"] in ("APP", "GLOBAL"):
                program_by_key[cmd["key"]] = cmd

        # 3) Merge (active app wins on duplicates, but GLOBAL keys should be unique anyway)
        merged: dict[str, dict] = {}
        merged.update(globals_by_key)
        merged.update(program_by_key)

        commands = sorted(merged.values(), key=lambda c: c["key"])
        projection = await self.on_project(
            name="overview.sam",
            state={
                "mode": "program",
                "commands": commands,
            },
        )
        yield out(projection)

    def resolve_man_mode(self, request: Request) -> str:
        if request.has_option("internal"):
            return "internal"
        if request.has_option("all"):
            return "all"
        return "default"


# ----------------------------------
# PORTS
# ----------------------------------


class OnListManual(Protocol):
    async def __call__(
        self,
        *,
        app_id: str,
        mode: str,
        kind: CommandKind | None = None,
    ) -> list[dict[str, Any]]: ...


class OnProjectManual(Protocol):
    async def __call__(
        self, resources: dict, name: str, state: dict | None = None
    ) -> Projection: ...


class OnGetActiveApp(Protocol):
    def __call__(self) -> str: ...


class OnListCommandsForApp(Protocol):
    def __call__(self, *, app_id: str) -> Sequence[type[Command]]: ...


class OnListCommandsForManual(Protocol):
    def __call__(
        self,
        *,
        app_id: str,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[type[Command]]: ...
