# yakoon/platform/runtime/message/spec.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Role = Literal["info", "success", "warning", "error", "help"]


@dataclass(frozen=True, slots=True)
class InlineText:
    """
    Plain inline text.

    Usage (YAML):
        - { type: "text", text: "Hello world" }
    """

    type: Literal["text"]
    text: str


@dataclass(frozen=True, slots=True)
class InlineCode:
    """
    Inline code fragment (semantic, not Markdown).

    Usage (YAML):
        - { type: "code", code: "man" }

    Console example:
        `man`
    """

    type: Literal["code"]
    code: str


@dataclass(frozen=True, slots=True)
class InlineLink:
    """
    Inline link (label + href).

    Usage (YAML):
        - { type: "link", text: "Docs", href: "https://example.com" }

    Console example:
        Docs (https://example.com)
    """

    type: Literal["link"]
    text: str
    href: str


Inline = InlineText | InlineCode | InlineLink


@dataclass(frozen=True, slots=True)
class TextBlock:
    """
    A paragraph-like text block.

    The `text` field may be:
        - a plain string
        - or a list of inline nodes

    Usage (simple):
        - type: text
          text: "Welcome to Yakoon"

    Usage (with inline):
        - type: text
          text:
            - { type: "text", text: "Start with " }
            - { type: "code", code: "man" }
    """

    type: Literal["text"]
    text: str | list[Inline]


@dataclass(frozen=True, slots=True)
class RuleBlock:
    """
    A horizontal rule (visual separator line).

    YAML:
        - type: rule
    """

    type: Literal["rule"]
    style: Literal["subtle", "normal", "strong"] = "normal"


@dataclass(frozen=True, slots=True)
class SpacerBlock:
    """
    Vertical spacing.

    YAML:
        - type: spacer
          size: 1   # optional, default = 1 blank line
    """

    type: Literal["spacer"]
    size: int = 1


@dataclass(frozen=True, slots=True)
class ListBlock:
    """
    A list block.

    Each list item may be:
        - a plain string
        - or a list of inline nodes

    Usage (simple):
        - type: list
          items:
            - "version - show system info"
            - "man - show help"

    Usage (inline items):
        - type: list
          items:
            - - { type: "code", code: "man" }
              - { type: "text", text: " - show help" }
    """

    type: Literal["list"]
    items: list[str | list[Inline]]


@dataclass(frozen=True, slots=True)
class KvBlock:
    """
    An ordered key–value block.

    Represents structured key–value pairs where order matters.

    Each item is a (key, value) tuple.
    Values are rendered strings (no nested structure).

    Usage (YAML):
        - type: kv
          items:
            - ["Platform Version", "v0.4.1"]
            - ["Python", "3.13.11"]

    Console example:
        Platform Version : v0.4.1
        Python           : 3.13.11
    """

    type: Literal["kv"]
    items: list[tuple[str, Any]]


Block = TextBlock | ListBlock | KvBlock | SpacerBlock | RuleBlock


@dataclass(frozen=True, slots=True)
class MessageSpec:
    """
    Canonical structured output specification.

    MessageSpec is the UI-agnostic representation of a message
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
