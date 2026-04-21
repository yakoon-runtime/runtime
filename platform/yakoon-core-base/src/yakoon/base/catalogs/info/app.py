from dataclasses import dataclass

from .controller import ControllerInfo


@dataclass(frozen=True, slots=True)
class AppInfo:
    id: str
    is_shell: bool
    is_listed: bool
    is_activatable: bool
    controllers: tuple[ControllerInfo, ...]
