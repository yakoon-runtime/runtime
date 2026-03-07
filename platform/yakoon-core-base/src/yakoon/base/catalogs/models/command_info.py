from dataclasses import dataclass

from yakoon.base.runtime.commands import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)


@dataclass(frozen=True, slots=True)
class CommandInfo:
    key: str
    kind: CommandKind
    scope: CommandScope
    visibility: CommandVisibility
    controller_id: str
    category: str
