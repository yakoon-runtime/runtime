from dataclasses import dataclass, field

from y5n.runtime.nodes import Mount


@dataclass
class RuntimeSettings:
    known: dict[str, str] = field(default_factory=dict)
    mounts: list[Mount] = field(default_factory=list)
