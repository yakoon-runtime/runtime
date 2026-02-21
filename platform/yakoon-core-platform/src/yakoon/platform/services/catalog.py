from __future__ import annotations

from collections.abc import Iterable, Sequence

from yakoon.base import ports
from yakoon.base.commands.command import CommandKind, CommandVisibility
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.catalog import CommandInfo, ControllerInfo
from yakoon.base.models.command import CommandScope
from yakoon.base.models.perm import Permission
from yakoon.base.ports import PermissionService
from yakoon.base.runtime.session.session import Session


class CommandCatalog:

    def __init__(self, commands: Iterable[CommandInfo]):
        self._commands: tuple[CommandInfo, ...] = tuple(commands)

    def all(self) -> tuple[CommandInfo, ...]:
        return self._commands


class CommandCatalogService:

    def __init__(self, services: ServiceDirectory, catalog: CommandCatalog):
        self._services = services
        self._catalog = catalog
        self._by_controller: dict[str, list[CommandInfo]] = {}
        self._global: tuple[CommandInfo, ...] = ()
        self._built = False

    def build(self) -> None:
        if self._built:
            return

        by_controller: dict[str, list[CommandInfo]] = {}
        global_cmds: dict[str, CommandInfo] = {}

        controllers = self._services.get(ports.ControllerCatalogService)

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
            raise RuntimeError("CommandCatalogService.build() was not called.")

    def all(self) -> tuple[CommandInfo, ...]:
        self._ensure_built()
        out: list[CommandInfo] = []
        for cid in sorted(self._by_controller.keys()):
            out.extend(self._by_controller[cid])
        return tuple(out)

    def for_resolve(
        self,
        active_controller_id: str,
    ) -> tuple[CommandInfo, ...]:
        """
        Deterministic resolve order using only CommandInfo:
          1) active controller CONTROLLER
          2) active controller SHELL (only if active controller is shell)
          3) GLOBAL across all controllers (unique by key)
        """
        self._ensure_built()

        controllers = self._services.get(ports.ControllerCatalogService)
        ctrl = controllers.get(active_controller_id)
        is_shell = bool(ctrl and ctrl.is_shell)

        out: list[CommandInfo] = []

        # 1) active controller CONTROLLER
        for c in self._by_controller.get(active_controller_id, ()):
            if c.scope == CommandScope.CONTROLLER:
                out.append(c)

        # 2) active controller SHELL
        if is_shell:
            for c in self._by_controller.get(active_controller_id, ()):
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
        perm_service = self._services.get(PermissionService)
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
        active_controller_id: str,
        command_key: str,
    ) -> CommandInfo | None:
        key = command_key.strip()
        for ci in self.for_resolve(active_controller_id):
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


class ControllerCatalog:

    def __init__(self, controllers: Iterable[ControllerInfo]):
        self._controllers = controllers

    def all(self):
        return self._controllers


class ControllerCatalogService:
    """
    Read-only snapshot about controller metadata.
    No controller instance, no directory references.
    """

    def __init__(self, catalog: ControllerCatalog):
        by_id: dict[str, ControllerInfo] = {}
        for c in catalog.all():
            if c.id in by_id:
                raise ValueError(f"Duplicate controller id in catalog: {c.id}")
            by_id[c.id] = c
        self._by_id = by_id

    def ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_id.keys()))

    def all(self) -> Sequence[ControllerInfo]:
        return tuple(self._by_id[cid] for cid in self.ids())

    def get(self, controller_id: str) -> ControllerInfo | None:
        return self._by_id.get(controller_id)

    def exists(self, controller_id: str) -> bool:
        return controller_id in self._by_id

    def activatable(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_activatable)

    def listed(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_listed)

    def shell(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_shell)

    def is_shell(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_shell)

    def is_activatable(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_activatable)

    def is_listed(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_listed)
