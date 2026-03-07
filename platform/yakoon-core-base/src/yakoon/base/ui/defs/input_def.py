from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .field_def import ViewFieldDef


@dataclass(frozen=True, slots=True)
class ViewInputDef:
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


InputDef = ViewInputDef
