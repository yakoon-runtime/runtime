# yakoon/platform/runtime/message/spec.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .inline import Inline


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
