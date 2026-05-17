from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from yakoon.base.errors import ErrorState

from .errors import UnknowOptionsError, UsageError
from .invocation import Invocation
from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:
    from .request import Request


class Command(ABC):
    """Base class for all executable commands."""

    # ----------------------------------
    # PUBLIC IDENTITY
    # ----------------------------------

    key: str
    usage_key: str = "--h"

    app: Any = None
    composer: Any = None
    group: Any = None

    anonymous = False

    # ----------------------------------
    # EXECUTION METADATA
    # ----------------------------------

    kind: CommandKind = CommandKind.USER
    scope: CommandScope = CommandScope.APP
    visibility: CommandVisibility = CommandVisibility.NORMAL

    invocations: list[Invocation] = []

    # ----------------------------------
    # INTERNAL
    # ----------------------------------

    @classmethod
    def _usage_data(
        cls,
        invocations: list[Invocation],
    ) -> list[dict]:

        return [invocation.usage_data(cls.key) for invocation in invocations]

    # ----------------------------------
    # VALIDATION
    # ----------------------------------

    @classmethod
    def ensure_invocation(
        cls,
        tokens: list[str] | None,
    ) -> None:

        if not cls.invocations:
            return

        tokens = tokens or []

        # ----------------------------------
        # SHOW USAGE
        # ----------------------------------

        if cls.usage_key and cls.usage_key in tokens:

            raise UsageError(
                ErrorState.by_type(
                    key=UsageError,
                    usages=cls._usage_data(cls.invocations),
                )
            )

        # ----------------------------------
        # INVOCATION MODES
        # ----------------------------------

        action_invocations = [x for x in cls.invocations if x.action]

        positional_invocations = [x for x in cls.invocations if not x.action]

        matching: list[Invocation] = []

        # ----------------------------------
        # ACTION COMMANDS
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

            raise UsageError(
                ErrorState.by_type(
                    key=UsageError,
                    usages=cls._usage_data(cls.invocations),
                )
            )

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

            unknown_options: list[str] = []

            for token in tokens[offset:]:

                if not token.startswith("--"):
                    continue

                key = token.split("=")[0]

                if key not in valid_options:
                    unknown_options.append(key)

            # ----------------------------------
            # UNKNOWN OPTIONS
            # ----------------------------------

            if unknown_options:

                raise UnknowOptionsError(
                    ErrorState.by_type(
                        key=UnknowOptionsError,
                        unknown_options=sorted(unknown_options),
                        valid_options=sorted(valid_options),
                        usages=cls._usage_data([invocation]),
                    )
                )

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return

        # ----------------------------------
        # INVALID INVOCATION
        # ----------------------------------

        raise UsageError(
            ErrorState.by_type(
                key=UsageError,
                usages=cls._usage_data(matching),
            )
        )

    # ----------------------------------
    # EXECUTION
    # ----------------------------------

    @abstractmethod
    def run(
        self,
        request: Request,
    ):
        raise NotImplementedError
