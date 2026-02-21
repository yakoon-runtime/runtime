from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LookupEntry:
    aliases: list[str]
    tags: list[str]


@dataclass(frozen=True, slots=True)
class LookupIndex:
    # command_key -> entry
    commands: dict[str, LookupEntry]
