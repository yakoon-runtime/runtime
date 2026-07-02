from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import UnknowOptionsError, UsageError


@dataclass(slots=True)
class Param:
    """A single named parameter within an Invocation."""

    key: str
    title: str = ""
    placeholder: str = ""
    default: Any = None
    help: str = ""
    policy: Any = None
    required: bool = False
    positional: bool = False


@dataclass(slots=True)
class Invocation:
    """A single command invocation: action + parameters.

    Matched against user input during node resolution.  The validator
    determines whether a token sequence fits this signature.
    """

    action: str | None = None
    params: list[Param] = field(default_factory=list)
    min_options: int = 0
    default: bool | None = None

    @property
    def arg_keys(self) -> list[str]:
        return [p.key for p in self.params if p.positional]

    @property
    def option_keys(self) -> list[str]:
        return [p.key for p in self.params if not p.positional]

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

    def bind(self, input: InvocationInput) -> BoundInvocation:
        """Bind concrete values, filling defaults as needed."""
        values = dict(input.values)
        for param in self.params:
            if param.key not in values:
                if param.default is not None:
                    values[param.key] = param.default
                elif param.required:
                    raise ValueError(f"Missing required parameter: {param.key!r}")
        return BoundInvocation(invocation=self, values=values)

    def has_required(self, tokens: list[str]) -> bool:
        """Check whether all required params are covered by *tokens*."""
        required_keys = {p.key for p in self.params if p.required}
        if not required_keys:
            return True

        missing = set(required_keys)
        positional_tokens = [t for t in tokens if not t.startswith("--")]

        pos_idx = 0
        for param in self.params:
            if not param.positional:
                continue
            if pos_idx < len(positional_tokens):
                missing.discard(param.key)
                pos_idx += 1

        for token in tokens:
            if token.startswith("--"):
                key = token.split("=")[0].removeprefix("--")
                missing.discard(key)

        return len(missing) == 0


@dataclass(frozen=True, slots=True)
class InvocationInput:
    """Raw key/value data produced by a Renderer (Form, Chat, …).

    Keys correspond to Param.key.  Values are the unconverted user input.
    """

    values: Mapping[str, Any]


@dataclass(slots=True)
class BoundInvocation:
    """A fully bound invocation with concrete values for every parameter."""

    invocation: Invocation
    values: Mapping[str, Any]


class InvocationValidator:

    def validate(
        self,
        node,
        tokens: list[str] | None,
        strict: bool = True,
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
            # POSITIONAL TOKENS
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

            # ----------------------------------
            # REQUIRED PARAMS
            # ----------------------------------

            num_positional = sum(1 for p in invocation.params if p.positional)

            if len(positional) > num_positional:
                continue

            required_keys = {p.key for p in invocation.params if p.required}
            provided: set[str] = set()

            pos_idx = 0
            for param in invocation.params:
                if not param.positional:
                    continue
                if pos_idx < len(positional):
                    provided.add(param.key)
                    pos_idx += 1

            for token in tokens[offset:]:
                if not token.startswith("--"):
                    continue
                key = token.split("=")[0].removeprefix("--")
                if key in required_keys:
                    provided.add(key)

            if strict and required_keys != provided:
                continue

            # ----------------------------------
            # OPTIONS
            # ----------------------------------

            valid_options = {f"--{x.key}" for x in invocation.params}

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

            if invocation.min_options > 0 and strict:

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
