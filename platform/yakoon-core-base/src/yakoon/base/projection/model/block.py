from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .action import Action
from .field import Field
from .inline import Inline

RuleStyle = Literal["subtle", "normal", "strong"]


@dataclass(frozen=True, slots=True)
class TextBlock:
    id: str | None = None
    type: Literal["text"] = "text"

    text: str | list[Inline] = ""
    style: str | None = None

    __stream_fields__ = ("text",)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ParagraphBlock:
    type: Literal["paragraph"] = "paragraph"
    id: str | None = None
    text: list[Inline] | None = None

    def children(self):
        return []


@dataclass(frozen=True, slots=True)
class HeadingBlock:
    type: Literal["heading"] = "heading"
    level: int = 1
    id: str | None = None
    text: list[Inline] | None = None

    def children(self):
        return []


@dataclass(frozen=True, slots=True)
class RuleBlock:
    id: str | None = None
    type: Literal["rule"] = "rule"

    style: RuleStyle = "normal"

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class SpacerBlock:
    id: str | None = None
    type: Literal["spacer"] = "spacer"

    size: int = 1

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ListBlock:
    id: str | None = None
    type: Literal["list"] = "list"

    items: list[ListItemBlock] = field(default_factory=list)

    def children(self):
        return tuple(self.items)


@dataclass(frozen=True, slots=True)
class ListItemBlock:
    id: str | None
    type: Literal["list_item"] = "list_item"

    text: str | list[Inline] = ""
    blocks: list[Block] | None = None

    __stream_fields__ = ("text",)

    def children(self):
        return tuple(self.blocks or ())


@dataclass(frozen=True, slots=True)
class KvBlock:
    id: str | None = None
    type: Literal["kv"] = "kv"

    items: list[KvItemBlock] = field(default_factory=list)

    def children(self):
        return tuple(self.items)


@dataclass(frozen=True, slots=True)
class KvItemBlock:
    id: str | None
    type: Literal["kv_item"] = "kv_item"

    key: str = ""
    value: list[Inline] = field(default_factory=list)

    __stream_fields__ = ("value",)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class TableBlock:
    id: str | None = None
    type: Literal["table"] = "table"

    headers: list[str] | None = None
    rows: list[list[str]] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return ()


FieldsState = Literal["idle", "active", "done"]


@dataclass(frozen=True, slots=True)
class FieldsBlock:
    """
    Interactive field collection inside the UI document.
    """

    id: str | None = None
    type: Literal["fields"] = "fields"
    name: str | None = None

    fields: list[Field] = field(default_factory=list)

    title: str | None = None
    step_key: str | None = None
    batch_id: str | None = None

    state: FieldsState = "idle"
    meta: dict[str, Any] | None = None

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ActionBlock:
    id: str | None = None
    type: Literal["actions"] = "actions"
    actions: list[Action] = field(default_factory=list)

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
    | ActionBlock
    | ParagraphBlock
    | HeadingBlock
)
