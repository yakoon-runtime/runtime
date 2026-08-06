from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import UnknownOptionsError, UsageError


@dataclass(slots=True)
class Param:
    """A single named parameter within a CommandSignature."""

    key: str
    title: str = ""
    placeholder: str = ""
    default: Any = None
    help: str = ""
    policy: Any = None
    required: bool = False
    positional: bool = False


@dataclass(slots=True)
class CommandSignature:
    """A declared way a command can be invoked: action + parameters.

    Declared in yak.yml (``invocation:``). Matched against user input
    during node resolution. A signature is a *description* — it says
    how a command may be called, it is not a concrete call.
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

    def bind(
        self,
        values: Mapping[str, Any],
        *,
        path: str,
        lang: str = "en",
    ) -> Invocation:
        """Bind concrete values into a concrete Invocation.

        Fills defaults as needed and builds the argument tokens. The
        command name lives in ``path`` — it is never duplicated into
        ``args`` (ADR-12: an invocation is ``path`` + ``args``).
        """
        filled = dict(values)
        for param in self.params:
            if param.key not in filled:
                if param.default is not None:
                    filled[param.key] = param.default
                elif param.required:
                    raise ValueError(f"Missing required parameter: {param.key!r}")

        args: list[str] = []
        for param in self.params:
            val = filled.get(param.key)
            if val is None:
                continue
            if param.positional:
                args.append(str(val))
            else:
                args.append(f"--{param.key}")
                args.append(str(val))

        return Invocation(path=path, args=args, lang=lang)

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
class Invocation:
    """A concrete call: what to execute and with what arguments.

    ``path`` answers *what is executed*; ``args`` answers *with what it
    is executed* (never the command name — that lives in ``path``).
    ``payload`` is the ADR-13 payload (``None`` for ordinary commands,
    the exception for error invocations, later timer/webhook).
    """

    path: str
    args: list[str] = field(default_factory=list)
    payload: Any | None = None
    lang: str = "en"


class CommandSignatureValidator:
    """Match token sequences against a node's declared signatures."""

    def validate(
        self,
        node,
        tokens: list[str] | None,
        strict: bool = True,
    ) -> CommandSignature | None:

        signatures = node.signatures

        if not signatures:
            return None

        tokens = tokens or []

        # ----------------------------------
        # GROUPS
        # ----------------------------------

        default_signatures = [x for x in signatures if x.default]

        action_signatures = [x for x in signatures if x.action is not None]

        positional_signatures = [
            x for x in signatures if not x.default and x.action is None
        ]

        matching: list[CommandSignature] = []

        # ----------------------------------
        # ACTION MATCHING
        # ----------------------------------

        if tokens:

            action = tokens[0]

            matching = [x for x in action_signatures if x.action == action]

        # ----------------------------------
        # DEFAULT MATCHING
        # ----------------------------------

        if not matching:

            matching = default_signatures

        # ----------------------------------
        # POSITIONAL MATCHING
        # ----------------------------------

        if not matching:

            matching = positional_signatures

        # ----------------------------------
        # NO MATCH
        # ----------------------------------

        if not matching:

            raise UsageError(
                usages=self._usage_data(
                    node,
                    signatures,
                ),
            )

        # ----------------------------------
        # OPTIONS KNOWN BY THE CANDIDATE SIGNATURES
        # ----------------------------------

        allowed_options = self._allowed_options(matching)
        self._raise_unknown_options(tokens, allowed_options, node, matching)

        # ----------------------------------
        # VALIDATE MATCHES
        # ----------------------------------

        for signature in matching:

            offset = 1 if signature.action else 0

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

            num_positional = sum(1 for p in signature.params if p.positional)

            if len(positional) > num_positional:
                continue

            required_keys = {p.key for p in signature.params if p.required}
            provided: set[str] = set()

            pos_idx = 0
            for param in signature.params:
                if not param.positional:
                    continue
                if pos_idx < len(positional):
                    if param.key in required_keys:
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
            # MIN OPTIONS
            # ----------------------------------

            valid_options = {f"--{x.key}" for x in signature.params}

            if signature.min_options > 0 and strict:

                option_count = 0
                for token in tokens[offset:]:
                    if not token.startswith("--"):
                        continue
                    key = token.split("=")[0]
                    if key in valid_options:
                        option_count += 1

                if option_count < signature.min_options:
                    continue

            # ----------------------------------
            # MATCH
            # ----------------------------------

            return signature

        # ----------------------------------
        # INVALID SIGNATURE
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

    @staticmethod
    def _allowed_options(signatures: list[CommandSignature]) -> set[str]:
        allowed: set[str] = set()
        for sig in signatures:
            for p in sig.params:
                if not p.positional:
                    allowed.add(f"--{p.key}")
        return allowed

    def _raise_unknown_options(
        self,
        tokens: list[str],
        allowed_options: set[str],
        node,
        matching: list[CommandSignature],
    ) -> None:
        unknown: list[str] = []
        for token in tokens or []:
            if not token.startswith("--"):
                continue
            key = token.split("=")[0]
            if key not in allowed_options:
                unknown.append(key)
        if unknown:
            raise UnknownOptionsError(
                unknown_options=sorted(unknown),
                valid_options=sorted(allowed_options),
                usages=self._usage_data(node, matching),
            )

    def _usage_data(
        self,
        node,
        signatures: list[CommandSignature],
    ) -> list[dict]:

        return [signature.usage_data(node.key) for signature in signatures]
