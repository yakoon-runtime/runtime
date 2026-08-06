from __future__ import annotations

import shlex

from y5n.runtime.api.runtime import Event
from y5n.runtime.api.runtime.invocation import Invocation


class InputParser:
    """Parse raw input events into command, tokens, and pipeline segments.

    When the event carries a pre-built ``Invocation`` (e.g. from a
    pipeline stage like ``Continue(next=Invocation(...))``) the command
    and tokens are taken directly, skipping string parsing.
    """

    def parse(self, event: Event) -> tuple[str, list[str], list[str]]:

        if isinstance(event.payload, Invocation):
            inv = event.payload
            return inv.path, list(inv.args), []

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

        # rest stays raw
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
