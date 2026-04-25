from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from yakoon.base.projection.model import Projection
from yakoon.base.resources import ResourceRef

if TYPE_CHECKING:
    from yakoon.base.application import Application


@dataclass(frozen=True)
class ModuleImport:
    on_project: OnProject


@dataclass(frozen=True)
class ModuleMeta:
    name: str
    version: str
    description: str


@dataclass(frozen=True)
class ModuleExport:
    meta: ModuleMeta
    app: Application


@dataclass(frozen=True, slots=True)
class LoadedModule:
    export: ModuleExport
    module_name: str


# ----------------------------------
# PORTS
# ----------------------------------


class OnProject(Protocol):
    async def __call__(
        self, *, resource: ResourceRef, state: dict | None = None
    ) -> Projection: ...
