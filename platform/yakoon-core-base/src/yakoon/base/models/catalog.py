from dataclasses import dataclass

from yakoon.base.models.command import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)
from yakoon.base.resources.reference import ResourceReferences


@dataclass(frozen=True, slots=True)
class CommandInfo:
    key: str
    kind: CommandKind
    scope: CommandScope
    visibility: CommandVisibility
    category: str | None = None
    controller_id: str | None = None


@dataclass(frozen=True, slots=True)
class ControllerInfo:
    id: str
    is_shell: bool = False
    is_activatable: bool = False
    is_listed: bool = True
    resources: ResourceReferences | None = None
