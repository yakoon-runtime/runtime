from __future__ import annotations

from typing import Any

import yaml

from yakoon.discovery.models.parser import LookupEntry, LookupIndex


def _norm_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for x in value:
        s = str(x).strip().lower()
        if s:
            out.append(s)
    return out


class LookupParser:

    def parse(self, text: str) -> LookupIndex:
        raw = yaml.safe_load(text) or {}
        if not isinstance(raw, dict):
            return LookupIndex(commands={})

        commands = raw.get("commands")
        if not isinstance(commands, dict):
            return LookupIndex(commands={})

        out: dict[str, LookupEntry] = {}

        for command_key, meta in commands.items():
            if not isinstance(command_key, str) or not isinstance(meta, dict):
                continue
            aliases = _norm_list(meta.get("aliases"))
            tags = _norm_list(meta.get("tags"))
            out[command_key] = LookupEntry(aliases=aliases, tags=tags)

        return LookupIndex(commands=out)
