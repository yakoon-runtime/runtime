from dataclasses import dataclass

from yakoon.base.controllers.resources import ResourceReferences

from .command import CommandInfo


@dataclass(frozen=True, slots=True)
class ControllerInfo:
    id: str
    is_shell: bool
    is_activatable: bool
    is_listed: bool
    resources: ResourceReferences

    commands: tuple[CommandInfo, ...]
