from __future__ import annotations

from collections import defaultdict
from typing import Any

import yaml
from y5n.base.capabilities.discovery import LookupEntry, LookupIndex


def _norm_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for x in value:
        s = str(x).strip().lower()
        if s:
            out.append(s)
    return out


class DefaultLookupParser:

    def parse(self, text: str) -> LookupIndex:
        raw = yaml.safe_load(text) or {}
        if not isinstance(raw, dict):
            return LookupIndex(commands={})

        commands = raw.get("commands")
        if not isinstance(commands, dict):
            return LookupIndex(commands={})

        out: dict[str, LookupEntry] = {}
        alias_map: dict[str, list[str]] = defaultdict(list)
        tag_map: dict[str, list[str]] = defaultdict(list)

        for command_key, meta in commands.items():
            if not isinstance(command_key, str) or not isinstance(meta, dict):
                continue

            aliases = _norm_list(meta.get("aliases"))
            tags = _norm_list(meta.get("tags"))

            out[command_key] = LookupEntry(
                aliases=aliases,
                tags=tags,
            )

            # Build reverse indexes
            for a in aliases:
                alias_map[a].append(command_key)

            for t in tags:
                tag_map[t].append(command_key)

        return LookupIndex(
            commands=out,
            alias_index=dict(alias_map),
            tag_index=dict(tag_map),
        )
