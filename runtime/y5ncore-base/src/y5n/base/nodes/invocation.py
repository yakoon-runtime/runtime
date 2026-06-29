from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import UnknowOptionsError, UsageError
from .request import Request


@dataclass(slots=True)
class Param:
    """A single named parameter within an Invocation."""

    key: str
    title: str = ""
    placeholder: str = ""
    default: Any = None
    help: str = ""
    policy: Any = None
    required: bool = True


@dataclass(slots=True)
class Invocation:
    """A single command invocation: action + args + options.

    Matched against user input during node resolution.  The validator
    determines whether a token sequence fits this signature.
    """

    action: str | None = None
    args: list[Param] = field(default_factory=list)
    options: list[Param] = field(default_factory=list)
    min_options: int = 0
    default: bool | None = None

    @property
    def arg_keys(self) -> list[str]:
        return [p.key for p in self.args]

    @property
    def option_keys(self) -> list[str]:
        return [p.key for p in self.options]

    def usage_data(
        self,
        key: str,
    ) -> dict:

        return {
            "key": key,
            "action": self.action,
            "args": self.arg_keys,
            "options": self.option_keys,
            "min_options": self.min_options,
        }


@dataclass(frozen=True, slots=True)
class InvocationInput:
    """Raw key/value data produced by a Renderer (Form, Chat, …).

    Keys correspond to Param.key.  Values are the unconverted user input.
    """

    values: dict[str, Any]


@dataclass(slots=True)
class BoundInvocation:
    """A fully bound invocation with concrete values for every parameter."""

    invocation: Invocation
    values: dict[str, Any]

    def to_request(self, command: str, lang: str) -> Request:
        tokens: list[str] = []
        if self.invocation.action:
            tokens.append(self.invocation.action)
        for param in self.invocation.args:
            val = self.values.get(param.key)
            if val is not None:
                tokens.append(str(val))
        for param in self.invocation.options:
            val = self.values.get(param.key)
            if val is not None:
                tokens.append(f"--{param.key}")
                tokens.append(str(val))

        return Request(command=command, tokens=tokens, payload=None, lang=lang)


def bind_invocation(
    invocation: Invocation,
    input: InvocationInput,
) -> BoundInvocation:
    """Bind concrete values to an Invocation, filling defaults as needed."""
    values = dict(input.values)
    for param in (*invocation.args, *invocation.options):
        if param.key not in values:
            if param.default is not None:
                values[param.key] = param.default
            elif param.required:
                raise ValueError(f"Missing required parameter: {param.key!r}")
    return BoundInvocation(invocation=invocation, values=values)


class InvocationValidator:

    def validate(
        self,
        node,
        tokens: list[str] | None,
    ) -> Invocation | None:

        invocations = node.invocations

        if not invocations:
            return None

        tokens = tokens or []

        # ----------------------------------
        # GROUPS
        # ----------------------------------

        default_invocations = [x for x in invocations if x.default]

        action_invocations = [x for x in invocations if x.action is not None]

        positional_invocations = [
            x for x in invocations if not x.default and x.action is None
        ]

        matching: list[Invocation] = []

        # ----------------------------------
        # ACTION MATCHING
        # ----------------------------------

        if tokens:

            action = tokens[0]

            matching = [x for x in action_invocations if x.action == action]

        # ----------------------------------
        # DEFAULT MATCHING
        # ----------------------------------

        if not matching:

            matching = default_invocations

        # ----------------------------------
        # POSITIONAL MATCHING
        # ----------------------------------

        if not matching:

            matching = positional_invocations

        # ----------------------------------
        # NO MATCH
        # ----------------------------------

        if not matching:

            raise UsageError(
                usages=self._usage_data(
                    node,
                    invocations,
                ),
            )

        # ----------------------------------
        # VALIDATE MATCHES
        # ----------------------------------

        for invocation in matching:

            offset = 1 if invocation.action else 0

            # ----------------------------------
            # POSITIONAL ARGS
            # ----------------------------------

            positional: list[str] = []
            i = offset
            while i < len(tokens):
                tok = tokens[i]
                if tok.startswith("--"):
                    i += 1
                    if i < len(tokens) and not tokens[i].startswith("--"):
                        i += 1
                    continue
                positional.append(tok)
                i += 1

            if len(positional) != len(invocation.args):
                continue

            # ----------------------------------
            # OPTIONS
            # ----------------------------------

            valid_options = {f"--{x.key}" for x in invocation.options}

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
                    unknown_options=sorted(unknown_options),
                    valid_options=sorted(valid_options),
                    usages=self._usage_data(
                        node,
                        [invocation],
                    ),
                )

            # ----------------------------------
            # MIN OPTIONS
            # ----------------------------------

            if invocation.min_options > 0:

                option_count = 0
                for token in tokens[offset:]:
                    if not token.startswith("--"):
                        continue
                    key = token.split("=")[0]
                    if key in valid_options:
                        option_count += 1

                if option_count < invocation.min_options:
                    continue

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return invocation

        # ----------------------------------
        # INVALID INVOCATION
        # ----------------------------------

        raise UsageError(
            usages=self._usage_data(
                node,
                matching,
            ),
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
