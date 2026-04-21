from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.catalogs import ApplicationQuery, CommandInfo
from yakoon.base.commands import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)
from yakoon.platform.runtime.sessions import Session


class CommandQueryBuilder:

    def __init__(
        self,
        app_query: ApplicationQuery,
        permission_service: PermissionService,
    ):
        self._app_query = app_query
        self._permission_service = permission_service
        self._by_controller: dict[str, list[CommandInfo]] = {}
        self._by_shell: tuple[CommandInfo, ...] = ()
        self._by_global: tuple[CommandInfo, ...] = ()
        self._built = False

    def build(self) -> None:
        if self._built:
            return

        by_controller: dict[str, list[CommandInfo]] = {}
        by_global: dict[str, CommandInfo] = {}
        by_shell: dict[str, CommandInfo] = {}

        for app in self._app_query.all():
            for controller in app.controllers:
                for c in controller.commands:
                    if not c.controller_id:
                        raise RuntimeError("CommandInfo.controller_id cannot be empty.")

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

    def _ensure_built(self) -> None:
        if not self._built:
            raise RuntimeError("CommandIndexBuilder.build() was not called.")

    def all(self) -> tuple[CommandInfo, ...]:
        self._ensure_built()
        out: list[CommandInfo] = []
        for cid in sorted(self._by_controller.keys()):
            out.extend(self._by_controller[cid])
        return tuple(out)

    def globals(self) -> tuple[CommandInfo, ...]:
        self._ensure_built()
        return tuple(c for c in self._by_global if c.scope == CommandScope.GLOBAL)

    def for_resolve_context(
        self,
        app_id: str,
    ) -> tuple[CommandInfo, ...]:
        """
        Deterministic resolve order using only CommandInfo:
          1) active app APPLICATION
          2) active app SHELL (only if active app is shell)
          3) GLOBAL across all applications (unique by key)
        """
        self._ensure_built()

        out: list[CommandInfo] = []

        app = self._app_query.get(app_id)
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

    def for_app(self, app_id: str) -> Sequence[CommandInfo]:
        self._ensure_built()

        out: list[CommandInfo] = []

        app = self._app_query.get(app_id)
        if not app:
            return out

        for c in app.controllers:
            out.extend(self._by_controller.get(c.id, ()))
        return tuple(out)

    def for_app_visible(self, app_id: str, session: Session) -> Sequence[CommandInfo]:
        self._ensure_built()
        out: list[CommandInfo] = []
        for cmd in self.for_app(app_id):
            fq_key = Permission.fq_key(app_id, cmd.key)
            if self._permission_service.can_read(session, fq_key):
                out.append(cmd)
        return out

    def for_man_entries(
        self,
        app_id: str,
        session: Session,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[CommandInfo]:
        self._ensure_built()
        out: list[CommandInfo] = []
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
    ) -> CommandInfo | None:
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
