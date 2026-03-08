from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LookupEntry:
    aliases: list[str]
    tags: list[str]


@dataclass
class LookupIndex:
    commands: dict[str, LookupEntry]
    alias_index: dict[str, list[str]] = field(default_factory=dict)
    tag_index: dict[str, list[str]] = field(default_factory=dict)
