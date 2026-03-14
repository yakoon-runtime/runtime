from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .fields import ViewFieldDef

RuleStyle = Literal["subtle", "normal", "strong"]


# -----------------------------
# Inline
# -----------------------------


@dataclass(frozen=True, slots=True)
class InlineText:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass(frozen=True, slots=True)
class InlineCode:
    type: Literal["code"] = "code"
    code: str = ""


@dataclass(frozen=True, slots=True)
class InlineLink:
    type: Literal["link"] = "link"
    text: str = ""
    href: str = ""


Inline = InlineText | InlineCode | InlineLink


# -----------------------------
# Blocks
# -----------------------------


@dataclass(frozen=True, slots=True)
class TextBlock:
    type: Literal["text"] = "text"
    text: str | list[Inline] = ""
    id: str | None = None
    style: str | None = None

    __stream_fields__ = ("text",)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class RuleBlock:
    type: Literal["rule"] = "rule"
    id: str | None = None
    style: RuleStyle = "normal"

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class SpacerBlock:
    type: Literal["spacer"] = "spacer"
    id: str | None = None
    size: int = 1

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ListBlock:
    type: Literal["list"] = "list"
    items: list[ListItemBlock] = field(default_factory=list)
    id: str | None = None

    def children(self):
        return tuple(self.items)


@dataclass(frozen=True, slots=True)
class ListItemBlock:
    type: Literal["list_item"] = "list_item"
    head: str | list[Inline] = ""
    blocks: list[Block] | None = None
    id: str | None = None

    __stream_fields__ = ("head",)

    def children(self):
        return tuple(self.blocks or ())


@dataclass(frozen=True, slots=True)
class KvBlock:
    type: Literal["kv"] = "kv"
    items: list[KvItemBlock] = field(default_factory=list)
    id: str | None = None

    def children(self):
        return tuple(self.items)


@dataclass(frozen=True, slots=True)
class KvItemBlock:
    type: Literal["kv_item"] = "kv_item"
    key: str = ""
    value: str | list[Block] = ""
    id: str | None = None

    __stream_fields__ = ("value",)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class TableBlock:
    type: Literal["table"] = "table"
    headers: list[str] | None = None
    rows: list[list[str]] = field(default_factory=list)
    id: str | None = None

    def children(self) -> tuple[Block, ...]:
        return ()


InputMode = Literal["prompt", "form"]
FieldsState = Literal["idle", "active", "done"]


@dataclass(frozen=True, slots=True)
class FieldsBlock:
    """
    Interactive field collection inside the UI document.

    input_mode:
      - prompt: sequential / blocking interaction
      - form:   visible input controls, no implicit wait
    """

    type: Literal["fields"] = "fields"
    fields: list[ViewFieldDef] = field(default_factory=list)
    input_mode: InputMode = "prompt"

    title: str | None = None
    id: str | None = None

    step_key: str | None = None
    batch_id: str | None = None

    state: FieldsState = "idle"
    meta: dict[str, Any] | None = None

    def children(self) -> tuple[Block, ...]:
        return ()


Block = (
    TextBlock
    | RuleBlock
    | SpacerBlock
    | ListItemBlock
    | ListBlock
    | KvItemBlock
    | KvBlock
    | TableBlock
    | FieldsBlock
)
