from __future__ import annotations

import shlex

from y5n.base.runtime import Event


class InputParser:

    def parse(self, event: Event) -> tuple[str, list[str], list[str]]:

        parts = self.split_pipes(event.payload)

        if not parts:
            return "", [], []

        # HEAD vorbereiten (für dispatch!)
        head = parts[0]
        all_tokens = shlex.split(head)

        cmd = all_tokens[0] if all_tokens else ""
        args = all_tokens[1:]

        # Rest bleibt roh
        pipeline = parts[1:]

        return cmd, args, pipeline

    def split_pipes(self, raw: str) -> list[str]:
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in raw:
            if char in ('"', "'"):
                if in_quotes and char == quote_char:
                    in_quotes = False
                    quote_char = None
                elif not in_quotes:
                    in_quotes = True
                    quote_char = char

            if char == "|" and not in_quotes:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current).strip())

        return parts
