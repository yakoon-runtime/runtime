from dataclasses import dataclass

from yakoon.base.commands import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)


@dataclass(frozen=True, slots=True)
class CommandInfo:
    key: str
    app_id: str
    controller_id: str

    kind: CommandKind
    scope: CommandScope
    visibility: CommandVisibility
    category: str
