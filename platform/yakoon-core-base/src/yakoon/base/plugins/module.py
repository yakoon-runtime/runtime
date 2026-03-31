from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yakoon.base.controllers import Controller
    from yakoon.base.runtime import Container


@dataclass(frozen=True)
class ModuleMeta:
    name: str
    version: str
    description: str


@dataclass(frozen=True)
class ModuleExport:
    meta: ModuleMeta
    controllers: list[type[Controller]]
    public_ports: list[type[Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LoadedModule:
    export: ModuleExport
    container: Container
    module_name: str
