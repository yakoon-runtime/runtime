from dataclasses import dataclass

from yakoon.base.controllers.resources import ResourceReferences


@dataclass(frozen=True, slots=True)
class ControllerInfo:
    id: str
    is_shell: bool
    is_activatable: bool
    is_listed: bool
    resources: ResourceReferences
