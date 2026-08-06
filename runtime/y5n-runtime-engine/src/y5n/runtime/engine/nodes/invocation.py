"""Token matching against a node's declared signatures (engine-internal).

The language (Param, CommandSignature, Invocation) lives in the Runtime
API. The validator works on Node (``node.signatures``, ``node.key``) and
is therefore engine logic, not public language.
"""

from __future__ import annotations

from y5n.runtime.api.runtime.invocation import CommandSignature

from .errors import UnknownOptionsError, UsageError


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


__all__ = ["CommandSignatureValidator"]
