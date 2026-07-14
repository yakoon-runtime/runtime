from dataclasses import dataclass, field


@dataclass
class RuntimeSettings:
    known: dict[str, str] = field(default_factory=dict)
    workspace_path: str = ""
