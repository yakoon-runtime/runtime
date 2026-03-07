from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .defs.input_def import InputDef
from .output_spec import OutputSpec
from .patch_spec import PatchSpec


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

    input: InputDef | None = None
    output: OutputSpec | None = None
    patch: PatchSpec | None = None

    meta: ViewMeta | None = None
