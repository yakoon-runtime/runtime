from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from y5n.base.application.application import Application
from y5n.base.commands import (
    Command,
    CommandScope,
)
from y5n.base.sources.request import DataRequest
from y5n.base.sources.source import DataResult, DataSource


class CommandSource(DataSource):

    def __init__(
        self,
        applications: Sequence[Application],
    ):
        self._commands: list[type[Command]] = []
        self._by_app: dict[str, list[type[Command]]] = {}
        self._by_scope: dict[CommandScope, list[type[Command]]] = {}

        self._build(applications)

        self._selectors = {
            "all": self._all,
            "by-app": self._by_app_selector,
            "global": self._global,
            "shell": self._shell,
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

        return handler(request)

    # ---------------------------------------------------------------------
    # Structural Resolvers
    # ---------------------------------------------------------------------

    def _all(
        self,
        request: DataRequest,
    ) -> DataResult:

        return DataResult.ok(rows=[self._to_row(cmd) for cmd in self._commands])

    def _by_app_selector(
        self,
        request: DataRequest,
    ) -> DataResult:

        app_id = request.option("by-app")

        cmds = self._by_app.get(app_id)

        if cmds is None:
            return DataResult.not_found(app_id=app_id)

        return DataResult.ok(rows=[self._to_row(cmd) for cmd in cmds])

    def _global(
        self,
        request: DataRequest,
    ) -> DataResult:

        cmds = self._by_scope.get(CommandScope.GLOBAL, [])

        return DataResult.ok(rows=[self._to_row(cmd) for cmd in cmds])

    def _shell(
        self,
        request: DataRequest,
    ) -> DataResult:

        cmds = self._by_scope.get(CommandScope.SHELL, [])

        return DataResult.ok(rows=[self._to_row(cmd) for cmd in cmds])

    # ---------------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------------

    def _allowed_visibilities(
        self,
        mode: str,
    ) -> set[str]:

        if mode == "default":
            return {"NORMAL"}

        if mode == "all":
            return {"NORMAL", "DEVELOPER"}

        if mode == "internal":
            return {"NORMAL", "DEVELOPER", "INTERNAL"}

        raise ValueError(f"invalid mode: {mode}")

    def _to_row(
        self,
        cmd: type[Command],
    ) -> dict[str, Any]:

        return {
            "key": cmd.key,
            "app_id": cmd.app.id,
            "scope": cmd.scope.name,
            "kind": cmd.kind.name,
            "visibility": cmd.visibility.name,
            "anonymous": cmd.anonymous,
        }

    def _build(
        self,
        applications: Sequence[Application],
    ):
        for app in applications:
            for composer in app.composers:
                for group in composer.command_groups:
                    for cmd in group.commands:
                        self._commands.append(cmd)
                        self._by_app.setdefault(app.id, []).append(cmd)
                        self._by_scope.setdefault(cmd.scope, []).append(cmd)
