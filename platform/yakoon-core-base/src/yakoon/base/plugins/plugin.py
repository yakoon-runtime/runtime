from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yakoon.base.runtime.controllers import Controller
    from yakoon.base.runtime.services import ServiceDirectory


@dataclass(frozen=True)
class PluginMeta:
    name: str
    version: str
    description: str


@dataclass(frozen=True)
class PluginExport:
    meta: PluginMeta
    controllers: list[type[Controller]]
    public_services: list[type[Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    export: PluginExport
    services: ServiceDirectory
    module_name: str
