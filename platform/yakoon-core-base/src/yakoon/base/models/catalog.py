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
    category: str
    controller_id: str


@dataclass(frozen=True, slots=True)
class ControllerInfo:
    id: str
    is_shell: bool
    is_activatable: bool
    is_listed: bool
    resources: ResourceReferences
