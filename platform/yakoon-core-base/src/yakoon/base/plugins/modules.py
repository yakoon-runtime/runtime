from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.nodes import Node

# ----------------------------------
# MODULE META
# ----------------------------------


@dataclass(frozen=True)
class ModuleMeta:
    """Static metadata describing a runtime module.

    Module metadata provides descriptive information about
    a semantic runtime module independently from its runtime
    composition.

    Metadata is used for discovery, diagnostics, inspection,
    versioning and platform tooling.
    """

    name: str
    version: str
    description: str


# ----------------------------------
# MODULE EXPORT
# ----------------------------------


@dataclass(frozen=True)
class ModuleExport:
    """Exports a semantic runtime module.

    A module export describes how a runtime node hierarchy
    is composed during platform initialization.

    The exported build function receives the root capability
    scope for the module and returns the composed runtime node.
    """

    meta: ModuleMeta
    node: Node | None = None


# ----------------------------------
# LOADED MODULE
# ----------------------------------


@dataclass(frozen=True, slots=True)
class LoadedModule:
    """Represents a loaded runtime module inside the platform.

    A loaded module combines the imported python module identity
    with its exported runtime composition definition.

    Loaded modules are resolved by the platform loader before
    runtime composition and node activation occur.
    """

    export: ModuleExport
    module_name: str
