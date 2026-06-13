from dataclasses import dataclass, field


@dataclass
class RuntimeSettings:
    plugins: list[str] = field(default_factory=list)
    known: dict[str, str] = field(default_factory=dict)
