# yakoon/platform/runtime/message/spec.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .blocks import Block

Role = Literal["info", "success", "warning", "error", "help"]


@dataclass(frozen=True, slots=True)
class OutputSpec:
    """
    Canonical structured output specification.

    OutputSpec is the UI-agnostic representation of a message
    emitted by the engine.

    It contains:
        - a semantic role (info, error, help, ...)
        - an optional title
        - a list of structured content blocks
        - optional metadata (non-rendering information)

    Must NOT contain presentation details such as:
        - ANSI codes
        - Markdown formatting
        - HTML fragments

    Example (YAML):

        kind: message
        role: info
        title: "System Status"
        blocks:
          - type: kv
            items:
              - ["Platform Version", "v0.4.1"]
              - ["Python", "3.13.11"]
        meta:
          code: "shell.version.show"

    Rendering is entirely the responsibility of the host.
    """

    kind: Literal["message"]
    role: Role
    title: str | None
    blocks: list[Block]
    meta: dict[str, Any] | None = None
    stream: Literal["none", "delta", "final"] = "none"
    error_kind: Literal["validation", "system"] | None = None
