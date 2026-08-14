from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ParamKind(StrEnum):
    """The syntactic form a parameter takes on the command line.

    ``VALUE`` is the default: the option is followed by exactly one
    value (``--world crm``). ``FLAG`` takes no value (``--twoway``).
    The vocabulary is closed; new forms (``list``, ``path``, ``enum``,
    …) extend the enum without changing the model.
    """

    VALUE = "value"
    FLAG = "flag"


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
    kind: ParamKind = ParamKind.VALUE


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
            "options": [
                p.key
                for p in self.params
                if not p.positional and p.kind is not ParamKind.FLAG
            ],
            "flags": [
                p.key
                for p in self.params
                if not p.positional and p.kind is ParamKind.FLAG
            ],
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
            elif param.kind is ParamKind.FLAG:
                if val:
                    args.append(f"--{param.key}")
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


__all__ = [
    "CommandSignature",
    "Invocation",
    "Param",
    "ParamKind",
]
