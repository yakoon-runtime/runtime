from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.catalogs import CommandCatalog, CommandInfo, ControllerRegistry
from yakoon.base.commands import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)
from yakoon.base.runtime import Container
from yakoon.platform.runtime.sessions import Session


class CommandIndexBuilder:

    def __init__(self, container: Container, catalog: CommandCatalog):
        self._container = container
        self._catalog = catalog
        self._by_controller: dict[str, list[CommandInfo]] = {}
        self._global: tuple[CommandInfo, ...] = ()
        self._built = False

    def build(self) -> None:
        if self._built:
            return

        by_controller: dict[str, list[CommandInfo]] = {}
        global_cmds: dict[str, CommandInfo] = {}

        controllers = self._container.get(ControllerRegistry)

        for c in self._catalog.all():
            if not c.controller_id:
                raise RuntimeError("CommandInfo.controller_id cannot be empty.")

            by_controller.setdefault(c.controller_id, []).append(c)

            if c.scope == CommandScope.GLOBAL:
                prev = global_cmds.get(c.key)
                if prev:
                    raise ValueError(
                        f"GLOBAL command key conflict: '{c.key}' "
                        f"({prev.controller_id} vs {c.controller_id})"
                    )
                global_cmds[c.key] = c

            if c.scope == CommandScope.SHELL:
                if not controllers.is_shell(c.controller_id):
                    raise ValueError(
                        f"SHELL scoped command '{c.key}' must belong to shell controller "
                        f"(found in '{c.controller_id}')"
                    )

        for items in by_controller.values():
            items.sort(key=lambda x: x.key)

        self._global = tuple(sorted(global_cmds.values(), key=lambda x: x.key))
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
        return tuple(c for c in self._global if c.scope == CommandScope.GLOBAL)

    def for_resolve_context(
        self,
        controller_id: str,
    ) -> tuple[CommandInfo, ...]:
        """
        Deterministic resolve order using only CommandInfo:
          1) active controller CONTROLLER
          2) active controller SHELL (only if active controller is shell)
          3) GLOBAL across all controllers (unique by key)
        """
        self._ensure_built()

        controller_infos = self._container.get(ControllerRegistry)
        controller = controller_infos.get(controller_id)
        is_shell = bool(controller and controller.is_shell)

        out: list[CommandInfo] = []

        # 1) active controller CONTROLLER
        for c in self._by_controller.get(controller_id, ()):
            if c.scope == CommandScope.CONTROLLER:
                out.append(c)

        # 2) active controller SHELL
        if is_shell:
            for c in self._by_controller.get(controller_id, ()):
                if c.scope == CommandScope.SHELL:
                    out.append(c)

        # 3) globals
        out.extend(self._global)

        return tuple(out)

    def for_controller(self, controller_id: str) -> Sequence[CommandInfo]:
        self._ensure_built()
        return tuple(self._by_controller.get(controller_id, ()))

    def for_controller_visible(
        self, controller_id: str, session: Session
    ) -> Sequence[CommandInfo]:
        self._ensure_built()
        out: list[CommandInfo] = []
        perm_service = self._container.get(PermissionService)
        for cmd in self.for_controller(controller_id):
            fq_key = Permission.fq_key(controller_id, cmd.key)
            if perm_service.can_read(session, fq_key):
                out.append(cmd)
        return out

    def for_man_entries(
        self,
        controller_id: str,
        session: Session,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[CommandInfo]:
        self._ensure_built()
        out: list[CommandInfo] = []
        allowed = self._allowed_visibilities(mode)
        for cmd in self.for_controller_visible(controller_id, session):
            if cmd.visibility not in allowed:
                continue
            if kind_filter and cmd.kind != kind_filter:
                continue
            out.append(cmd)
        return out

    def resolve_info(
        self,
        controller_id: str,
        command_key: str,
    ) -> CommandInfo | None:
        key = command_key.strip()
        for ci in self.for_resolve_context(controller_id):
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
