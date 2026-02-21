from collections.abc import Iterable, Sequence

from yakoon.base.commands.command import CommandKind, CommandVisibility
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.catalog import CommandInfo, ControllerInfo
from yakoon.base.models.perm import Permission
from yakoon.base.ports import PermissionService
from yakoon.base.runtime.session.session import Session


class CommandCatalog:

    def __init__(self, commands: Iterable[CommandInfo]):
        self._commands: tuple[CommandInfo, ...] = tuple(commands)

    def all(self) -> tuple[CommandInfo, ...]:
        return self._commands


class CommandCatalogService:

    __slots__ = ("_services", "_by_controller")

    def __init__(self, services: ServiceDirectory, catalog: CommandCatalog):
        self._services = services
        by_controller: dict[str, list[CommandInfo]] = {}
        for c in catalog.all():
            if not c.controller_id:
                raise RuntimeError("Controller id cannot be none or empty.")
            by_controller.setdefault(c.controller_id, []).append(c)

        # stabile Ordnung
        for _, items in by_controller.items():
            items.sort(key=lambda x: x.key)

        self._by_controller = by_controller

    def for_controller(self, controller_id: str) -> Sequence[CommandInfo]:
        return tuple(self._by_controller.get(controller_id, ()))

    def keys_for_controller(self, controller_id: str) -> Sequence[str]:
        return tuple(c.key for c in self.for_controller(controller_id))

    def for_controller_visible(
        self, controller_id: str, session: Session
    ) -> Sequence[CommandInfo]:
        out = []
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
        out = []
        allowed = self._allowed_visibilities(mode)
        for cmd in self.for_controller_visible(controller_id, session):
            if cmd.visibility not in allowed:
                continue
            if kind_filter and cmd.kind != kind_filter:
                continue
            out.append(cmd)
        return out

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

    __slots__ = ("_by_id",)

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
