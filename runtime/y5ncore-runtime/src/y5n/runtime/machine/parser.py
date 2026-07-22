from __future__ import annotations

import shlex

from y5n.runtime.engine.nodes import Request
from y5n.runtime.engine.runtime import Event


class InputParser:
    """Parse raw input events into command, tokens, and pipeline segments.

    When the event carries a pre-built ``Request`` object (e.g. from a
    pipeline stage like ``Continue(next=Request(...))``) the command and
    tokens are taken directly, skipping string parsing.
    """

    def parse(self, event: Event) -> tuple[str, list[str], list[str]]:

        if isinstance(event.payload, Request):
            req = event.payload
            return req.command, list(req.args()), []

        if not isinstance(event.payload, str) or not event.payload.strip():
            return "", [], []

        parts = self.split_pipes(event.payload)

        if not parts:
            return "", [], []

        # Prepare HEAD (for dispatch!)
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
