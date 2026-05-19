from __future__ import annotations

from dataclasses import dataclass, field

from yakoon.base.errors import ErrorState

from .errors import UnknowOptionsError, UsageError


@dataclass(slots=True)
class Invocation:

    action: str | None = None
    args: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    default: bool | None = None

    def usage_data(
        self,
        key: str,
    ) -> dict:

        return {
            "key": key,
            "action": self.action,
            "args": self.args,
            "options": self.options,
        }


class InvocationValidator:

    def validate(
        self,
        node,
        tokens: list[str] | None,
    ) -> Invocation | None:

        invocations = node.invocations

        if not invocations:
            return

        tokens = tokens or []

        # ----------------------------------
        # ACTION INVOCATIONS
        # ----------------------------------

        action_invocations = [x for x in invocations if x.action]

        positional_invocations = [x for x in invocations if not x.action]

        matching: list[Invocation] = []

        # ----------------------------------
        # ACTION MATCHING
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
        # POSITIONAL INVOCATIONS
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
                    usages=self._usage_data(
                        node,
                        invocations,
                    ),
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
                        usages=self._usage_data(
                            node,
                            [invocation],
                        ),
                    )
                )

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return invocation

        # ----------------------------------
        # INVALID INVOCATION
        # ----------------------------------

        raise UsageError(
            ErrorState.by_type(
                key=UsageError,
                usages=self._usage_data(
                    node,
                    matching,
                ),
            )
        )

    # ----------------------------------
    # HELPERS
    # ----------------------------------

    def _usage_data(
        self,
        node,
        invocations: list[Invocation],
    ) -> list[dict]:

        return [invocation.usage_data(node.key) for invocation in invocations]
