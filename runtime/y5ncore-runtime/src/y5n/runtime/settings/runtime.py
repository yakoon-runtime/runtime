from dataclasses import dataclass, field


@dataclass
class RuntimeSettings:
    spaces: list[str] = field(default_factory=list)
    known: dict[str, str] = field(default_factory=dict)
    root_path: str = ""
