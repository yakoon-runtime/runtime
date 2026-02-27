# yakoon/platform/runtime/message/spec.py

from __future__ import annotations

from dataclasses import dataclass, field
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
    text: str | list[Inline] = ""
    id: str | None = None


@dataclass(frozen=True, slots=True)
class RuleBlock:
    """
    A horizontal rule (visual separator line).

    YAML:
        - type: rule
    """

    type: Literal["rule"]
    style: Literal["subtle", "normal", "strong"] = "normal"
    id: str | None = None


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
    id: str | None = None


@dataclass(frozen=True, slots=True)
class ListItemBlock:
    type: Literal["list_item"] = "list_item"
    head: str | list[Inline] = ""
    blocks: list[Block] | None = None
    id: str | None = None


@dataclass(frozen=True, slots=True)
class ListBlock:
    type: Literal["list"] = "list"
    items: list[ListItemBlock] = field(default_factory=list)
    id: str | None = None


@dataclass(frozen=True, slots=True)
class KvItemBlock:
    # kv_item = single key/value row; value may contain text or nested blocks
    type: Literal["kv_item"] = "kv_item"
    key: str = ""
    value: str | list[Any] | None = None
    id: str | None = None


@dataclass(frozen=True, slots=True)
class KvBlock:
    # kv = 2-column key/value container (modern UI layout, value streamable)
    type: Literal["kv"] = "kv"
    items: list[KvItemBlock] = field(default_factory=list)
    id: str | None = None


@dataclass(frozen=True, slots=True)
class TableBlock:
    """
    - type: table
    headers: ["Command", "Controller", "Score", "Reason"]
    rows:
        - ["man", "system", "0.92", "alias match"]
        - ["use", "shell", "0.61", "tag match"]
    """

    type: Literal["table"]
    headers: list[str] | None = None
    rows: list[list[str]] = field(default_factory=list)
    id: str | None = None


Block = (
    TextBlock
    | SpacerBlock
    | RuleBlock
    | ListBlock
    | ListItemBlock
    | KvBlock
    | TableBlock
)


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
    stream: Literal["none", "delta", "final"] = "none"
