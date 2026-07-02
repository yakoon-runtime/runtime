from __future__ import annotations

from ..invocation import BoundInvocation
from .request import Request


class RequestBuilder:
    """Builds a CLI-style Request from a BoundInvocation.

    Keeping this separate from BoundInvocation keeps the latter
    free of output-format concerns.
    """

    def build(
        self,
        bound: BoundInvocation,
        command: str,
        lang: str,
    ) -> Request:
        tokens: list[str] = []

        if bound.invocation.action:
            tokens.append(bound.invocation.action)

        for param in bound.invocation.params:
            val = bound.values.get(param.key)
            if val is not None:
                if param.positional:
                    tokens.append(str(val))
                else:
                    tokens.append(f"--{param.key}")
                    tokens.append(str(val))

        return Request(command=command, tokens=tokens, payload=None, lang=lang)
