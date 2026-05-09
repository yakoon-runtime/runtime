from __future__ import annotations

from abc import ABC, abstractmethod
from textwrap import dedent
from typing import TYPE_CHECKING

from .invocation import Invocation
from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:
    from .request import Request

from .errors import UsageError


class Command(ABC):
    """Base class for all executable commands."""

    # Public identity
    key: str

    app_id: str
    controller_id: str

    anonymous = False

    # Execution metadata
    kind: CommandKind = CommandKind.USER
    scope: CommandScope = CommandScope.APP
    visibility: CommandVisibility = CommandVisibility.NORMAL

    invocations: list[Invocation] = []

    @classmethod
    def ensure_invocation(
        cls,
        tokens: list[str] | None,
    ) -> None:

        if not cls.invocations:
            return

        tokens = tokens or []
        for invocation in cls.invocations:

            offset = 0

            # ----------------------------------
            # ACTION
            # ----------------------------------

            if invocation.action:

                if not tokens:
                    continue

                if tokens[0] != invocation.action:
                    continue

                offset = 1

            # ----------------------------------
            # POSITIONAL ARGS
            # ----------------------------------

            positional = [x for x in tokens[offset:] if not x.startswith("--")]
            if len(positional) < len(invocation.args):
                continue

            # ----------------------------------
            # OPTIONS
            # ----------------------------------

            valid_options = {f"--{x}" for x in invocation.options}

            unknown_options = []
            for token in tokens[offset:]:

                if not token.startswith("--"):
                    continue

                key = token.split("=")[0]
                if key not in valid_options:
                    unknown_options.append(key)

            if unknown_options:
                opts = "\n".join(f"  {x}" for x in sorted(valid_options))
                unknown = "\n".join(f"  {x}" for x in unknown_options)
                raise UsageError(dedent(f"""
                    Unknown option(s):
                    {unknown}

                    Supported options:
                    {opts}

                    {invocation.usage(cls.key)}
                    """).strip())

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return

        # ----------------------------------
        # NO MATCH
        # ----------------------------------

        matching = []

        if tokens:
            action = tokens[0]

            matching = [
                invocation
                for invocation in cls.invocations
                if invocation.action == action
            ]

        target = matching or cls.invocations
        usages = "\n".join(invocation.usage(cls.key) for invocation in target)
        raise UsageError(dedent(f"{usages}").strip())

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
