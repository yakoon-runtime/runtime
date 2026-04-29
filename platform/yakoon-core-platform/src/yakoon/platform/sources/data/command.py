from __future__ import annotations

from collections.abc import Sequence

from typing_extensions import Protocol

from yakoon.base.application.application import Application
from yakoon.base.capabilities.identity import Permission
from yakoon.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
)
from yakoon.base.sources.request import DataRequest
from yakoon.base.sources.source import DataResult, DataSource
from yakoon.platform.runtime.sessions import Session


class CommandQueryBuilder(DataSource):

    def __init__(
        self,
        applications: Sequence[Application],
        on_has_read_permission: OnHasReadPermission,
    ):
        self.applications = applications
        self.on_has_read_permission = on_has_read_permission

        self._by_controller: dict[str, list[type[Command]]] = {}
        self._by_shell: tuple[type[Command], ...] = ()
        self._by_global: tuple[type[Command], ...] = ()
        self._built = False
        self._build()

    def _build(self) -> None:
        if self._built:
            return

        by_controller: dict[str, list[type[Command]]] = {}
        by_global: dict[str, type[Command]] = {}
        by_shell: dict[str, type[Command]] = {}

        for app in self.applications:
            for controller in app.controllers:
                commands = []
                for commandset in controller.commandsets:
                    for command in commandset.commands:
                        command.app_id = app.id
                        command.controller_id = controller.id
                        commands.append(command)

                for c in commands:
                    by_controller.setdefault(c.controller_id, []).append(c)

                    if c.scope == CommandScope.GLOBAL:
                        prev = by_global.get(c.key)
                        if prev:
                            raise ValueError(
                                f"GLOBAL command key conflict: '{c.key}' "
                                f"({prev.controller_id} vs {c.controller_id})"
                            )
                        by_global[c.key] = c

                    if c.scope == CommandScope.SHELL:
                        prev = by_shell.get(c.key)
                        if prev:
                            raise ValueError(
                                f"SHELL command key conflict: '{c.key}' "
                                f"({prev.controller_id} vs {c.controller_id})"
                            )
                        by_shell[c.key] = c

                for items in by_controller.values():
                    items.sort(key=lambda x: x.key)

                self._by_shell = tuple(sorted(by_shell.values(), key=lambda x: x.key))
                self._by_global = tuple(sorted(by_global.values(), key=lambda x: x.key))
                self._by_controller = by_controller
                self._built = True

    async def read(self, request: DataRequest) -> DataResult:
        return DataResult(rows=[])

    def _ensure_built(self) -> None:
        if not self._built:
            raise RuntimeError("CommandIndexBuilder.build() was not called.")

    def all(self) -> tuple[type[Command], ...]:
        self._ensure_built()
        out: list[type[Command]] = []
        for cid in sorted(self._by_controller.keys()):
            out.extend(self._by_controller[cid])
        return tuple(out)

    def globals(self) -> tuple[type[Command], ...]:
        self._ensure_built()
        return tuple(c for c in self._by_global if c.scope == CommandScope.GLOBAL)

    def for_resolve_context(
        self,
        app_id: str,
    ) -> tuple[type[Command], ...]:
        """
        Deterministic resolve order using only type[Command]:
          1) active app APPLICATION
          2) active app SHELL (only if active app is shell)
          3) GLOBAL across all applications (unique by key)
        """
        self._ensure_built()

        out: list[type[Command]] = []

        app = next((a for a in self.applications if a.id == app_id), None)
        if not app:
            return tuple(out)

        # 1) all commands in active application
        for controller in app.controllers:
            for c in self._by_controller.get(controller.id, ()):
                if c.scope == CommandScope.APP:
                    out.append(c)

        # 2) all shell commands if app is shell
        if app.is_shell:
            out.extend(self._by_shell)

        # 3) global commands
        out.extend(self._by_global)

        return tuple(out)

    def for_app(self, app_id: str) -> Sequence[type[Command]]:
        self._ensure_built()

        out: list[type[Command]] = []

        app = next((a for a in self.applications if a.id == app_id), None)
        if not app:
            return out

        for c in app.controllers:
            out.extend(self._by_controller.get(c.id, ()))
        return tuple(out)

    def for_app_visible(self, app_id: str, session: Session) -> Sequence[type[Command]]:
        self._ensure_built()
        out: list[type[Command]] = []
        for cmd in self.for_app(app_id):
            fq_key = Permission.fq_key(app_id, cmd.key)
            if self.on_has_read_permission(session=session, perm_key=fq_key):
                out.append(cmd)
        return out

    def for_man_entries(
        self,
        app_id: str,
        session: Session,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[type[Command]]:
        self._ensure_built()
        out: list[type[Command]] = []
        allowed = self._allowed_visibilities(mode)
        for cmd in self.for_app_visible(app_id, session):
            if cmd.visibility not in allowed:
                continue
            if kind_filter and cmd.kind != kind_filter:
                continue
            out.append(cmd)
        return out

    def for_context(
        self,
        app_id: str,
        command_key: str,
    ) -> type[Command] | None:
        key = command_key.strip()
        for ci in self.for_resolve_context(app_id):
            if ci.key == key:
                return ci
        return None

    def _allowed_visibilities(self, mode: str) -> set[CommandVisibility]:
        if mode == "default":
            return {CommandVisibility.NORMAL}
        if mode == "all":
            return {CommandVisibility.NORMAL, CommandVisibility.DEVELOPER}
        if mode == "internal":
            return {
                CommandVisibility.NORMAL,
                CommandVisibility.DEVELOPER,
                CommandVisibility.INTERNAL,
            }
        raise ValueError(mode)


# ----------------------------------
# PORTS
# ----------------------------------


class OnHasReadPermission(Protocol):
    def __call__(self, *, session: Session, perm_key: str) -> bool: ...
