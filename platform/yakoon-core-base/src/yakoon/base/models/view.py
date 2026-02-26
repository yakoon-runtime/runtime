# yakoon/platform/runtime/view/spec.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from yakoon.base.models.message import Block, MessageSpec


@dataclass(frozen=True, slots=True)
class PatchReset:
    op: Literal["reset"] = "reset"


@dataclass(frozen=True, slots=True)
class PatchAppendBlock:
    op: Literal["append_block"] = "append_block"
    block: Block | None = None


@dataclass(frozen=True, slots=True)
class PatchAppendText:
    op: Literal["append_text"] = "append_text"
    block_id: str = ""
    text: str = ""


@dataclass(frozen=True, slots=True)
class PatchAppendChild:
    op: Literal["append_child"] = "append_child"
    block_id: str = ""
    parent_id: str = ""
    block: Block | None = None


PatchOp = PatchReset | PatchAppendBlock | PatchAppendText | PatchAppendChild


@dataclass(frozen=True, slots=True)
class PatchSpec:
    ops: list[PatchOp] = field(default_factory=list)
    final: bool = False


@dataclass(frozen=True, slots=True)
class ViewFieldDef:
    """
    Describes one input field as authored in a View template.

    Note:
        - It's the canonical authoring-time definition used in ViewSpec.input.
    """

    policy: str
    title: str | None = None
    required: bool = False
    var: str | None = None

    hint: str = ""
    default: str = ""
    pattern: str = ""

    ui: dict[str, Any] | None = None  # <- neu

    # Optional extensions (keep cheap):
    type: str | None = None  # e.g. "string", "int" (if you want)
    options: list[dict[str, str]] | None = None  # e.g. [{"value":"x","label":"X"}]


@dataclass(frozen=True, slots=True)
class ViewFormDef:
    """
    Canonical form definition within a View.

    Fields are a mapping so template authors can write:

        fields:
          ask1:
            policy: system:string
            title: "Ask1"
            required: true
            var: var.ask1
    """

    kind: Literal["form"]
    form_id: str
    fields: dict[str, ViewFieldDef]

    input_mode: Literal["prompt", "form"] = "prompt"

    title: str | None = None
    step_key: str | None = None
    batch_id: str | None = None
    meta: dict[str, Any] | None = None


InputDef = ViewFormDef


@dataclass(frozen=True, slots=True)
class ViewUI:
    secret: bool = False  # für Fields; bei Message später optional
    # später: focus, disabled, placeholder, etc.


@dataclass(frozen=True, slots=True)
class ViewMeta:
    ui: ViewUI | None


ViewMode = Literal["replace", "append", "patch"]


@dataclass(frozen=True, slots=True)
class ViewSpec:
    """
    Canonical view contract.

    A host receives exactly this structure (as dict/JSON eventually).
    It may contain:
        - message: what to display
        - input: what to ask/collect
    """

    kind: Literal["view"]
    mode: ViewMode = "replace"
    id: str | None = None

    message: MessageSpec | None = None
    input: InputDef | None = None
    meta: ViewMeta | None = None
    patch: PatchSpec | None = None
