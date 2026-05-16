from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.application import Application
    from yakoon.base.nodes import Node


@dataclass(frozen=True)
class ModuleMeta:
    name: str
    version: str
    description: str


@dataclass(frozen=True)
class ModuleExport:
    meta: ModuleMeta
    app: type[Application]
    node: Node | None = None


@dataclass(frozen=True, slots=True)
class LoadedModule:
    export: ModuleExport
    module_name: str
