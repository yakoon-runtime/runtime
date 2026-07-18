from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .action import Action
from .field import Field
from .inline import Inline, InlineText

RuleStyle = Literal["subtle", "normal", "strong"]
FieldsState = Literal["idle", "active", "done"]


# -----------------
# TEXT / CONTENT
# -----------------


@dataclass(frozen=True, slots=True)
class TextBlock:
    id: str | None = None
    type: Literal["text"] = "text"

    text: list[Inline] = field(default_factory=list)
    style: str | None = None

    def children(self) -> tuple[Block, ...]:
        return ()

    @classmethod
    def create(cls, *, text) -> TextBlock:
        return cls(text=[InlineText("text", text)])


@dataclass(frozen=True, slots=True)
class PreBlock:
    """Preformatted text"""

    id: str | None = None
    type: Literal["pre"] = "pre"

    code: str = ""
    language: str | None = None

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ParagraphBlock:
    type: Literal["paragraph"] = "paragraph"
    id: str | None = None

    text: list[Inline] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class HeadingBlock:
    type: Literal["heading"] = "heading"
    level: int = 1
    id: str | None = None

    text: list[Inline] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return ()


# -----------------
# SIMPLE BLOCKS
# -----------------


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


# -----------------
# LIST
# -----------------


@dataclass(frozen=True, slots=True)
class ListItemBlock:
    id: str | None = None
    type: Literal["list_item"] = "list_item"

    text: list[Inline] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.blocks)


@dataclass(frozen=True, slots=True)
class ListBlock:
    id: str | None = None
    type: Literal["list"] = "list"

    items: list[ListItemBlock] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.items)


# -----------------
# KEY VALUE
# -----------------


@dataclass(frozen=True, slots=True)
class KvItemBlock:
    id: str | None = None
    type: Literal["kv_item"] = "kv_item"

    key: str = ""
    value: list[Inline] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class KvBlock:
    id: str | None = None
    type: Literal["kv"] = "kv"

    items: list[KvItemBlock] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.items)


# -----------------
# DATA
# -----------------


@dataclass(frozen=True, slots=True)
class DataBlock:
    type: Literal["data"] = "data"
    id: str | None = None

    data: Any = None

    def children(self) -> tuple[Block, ...]:
        return ()


# -----------------
# TABLE
# -----------------


@dataclass(frozen=True, slots=True)
class TableColumn:
    key: str = ""
    title: str = ""


@dataclass(frozen=True, slots=True)
class TableBlock:
    """
    usage:
        <table>
        <column key="name" title="Name"/>
        <column key="age" title="Age"/>
        <row>
            <cell>Stefan</cell>
            <cell>42</cell>
        </row>
        <row>
            <cell>Anna</cell>
            <cell>31</cell>
        </row>
        </table>
    """

    id: str | None = None
    type: Literal["table"] = "table"

    columns: list[TableColumn] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)

    variant: str | None = None
    selectable: bool = True

    def children(self) -> tuple[Block, ...]:
        return ()


# -----------------
# INTERACTION
# -----------------


@dataclass(frozen=True, slots=True)
class FieldsBlock:
    id: str | None = None
    type: Literal["fields"] = "fields"

    name: str | None = None
    fields: list[Field] = field(default_factory=list)

    title: str | None = None
    intro: str | None = None
    step_key: str | None = None
    batch_id: str | None = None

    state: FieldsState = "idle"
    meta: dict[str, Any] = field(default_factory=dict)

    def children(self) -> tuple[Block, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class ActionBlock:
    id: str | None = None
    type: Literal["actions"] = "actions"

    actions: list[Action] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return ()


# -----------------
# CONTAINERS
# -----------------


@dataclass(frozen=True, slots=True)
class SectionBlock:
    type: Literal["section"] = "section"
    id: str | None = None

    blocks: list[Block] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.blocks)


@dataclass(frozen=True, slots=True)
class StackBlock:
    type: Literal["stack"] = "stack"
    id: str | None = None

    blocks: list[Block] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.blocks)


@dataclass(frozen=True, slots=True)
class FlowBlock:
    type: Literal["flow"] = "flow"
    id: str | None = None

    blocks: list[Block] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.blocks)


@dataclass(frozen=True, slots=True)
class CollapsibleBlock:
    """
    usage:
        <collapsible title="Analyse"></collapsible>
    """

    type: Literal["collapsible"] = "collapsible"
    id: str | None = None

    title: list[Inline] = field(default_factory=list)
    expanded: bool = False
    blocks: list[Block] = field(default_factory=list)

    def children(self) -> tuple[Block, ...]:
        return tuple(self.blocks)


# -----------------
# MEDIA
# -----------------


@dataclass(frozen=True, slots=True)
class ImageBlock:
    type: Literal["image"] = "image"
    id: str | None = None

    ref: str = ""
    src: str | None = None
    alt: str | None = None

    def children(self) -> tuple[Block, ...]:
        return ()


# -----------------
# UNION
# -----------------

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
    | SectionBlock
    | StackBlock
    | FlowBlock
    | CollapsibleBlock
    | PreBlock
    | ImageBlock
)
