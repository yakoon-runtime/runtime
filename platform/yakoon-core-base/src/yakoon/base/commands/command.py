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
    usage_key: str = "--h"

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

        # ----------------------------------
        # SHOW USAGE BY KEY
        # ----------------------------------

        if cls.usage_key and cls.usage_key in tokens:
            usages = "\n".join(
                invocation.usage(cls.key) for invocation in cls.invocations
            )
            raise UsageError(dedent(f"{usages}").strip())

        # ----------------------------------
        # INVOCATION MODES
        # ----------------------------------

        action_invocations = [x for x in cls.invocations if x.action]
        positional_invocations = [x for x in cls.invocations if not x.action]
        matching: list[Invocation] = []

        # ----------------------------------
        # ACTION-BASED COMMANDS
        # ----------------------------------

        if action_invocations:

            action = tokens[0] if tokens else None
            matching = [x for x in action_invocations if x.action == action]

            # ----------------------------------
            # DEFAULT INVOCATION
            # ----------------------------------

            if not matching and not tokens:
                default = next(
                    (x for x in action_invocations if x.default),
                    None,
                )
                if default:
                    matching = [default]

        # ----------------------------------
        # POSITIONAL COMMANDS
        # ----------------------------------

        else:

            matching = positional_invocations

        # ----------------------------------
        # NO MATCH
        # ----------------------------------

        if not matching:

            usages = "\n".join(
                invocation.usage(cls.key) for invocation in cls.invocations
            )

            raise UsageError(dedent(f"{usages}").strip())

        # ----------------------------------
        # VALIDATE MATCHES
        # ----------------------------------

        for invocation in matching:

            offset = 1 if invocation.action else 0

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

                raise UsageError(
                    dedent(
                        f"Unknown option(s):\n{unknown}\nSupported options:\n{opts}\n{invocation.usage(cls.key)}"
                    ).strip()
                )

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return

        # ----------------------------------
        # INVALID INVOCATION
        # ----------------------------------

        usages = "\n".join(invocation.usage(cls.key) for invocation in matching)
        raise UsageError(dedent(f"{usages}").strip())

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
