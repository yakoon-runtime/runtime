from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


@dataclass(frozen=True, slots=True)
class InputFieldDef:
    var: str
    policy: str = "system:string"
    title: str = ""
    required: bool = True
    default: Any | None = None
    options: list[dict[str, Any]] = field(default_factory=list)  # label/value dicts


@dataclass(frozen=True, slots=True)
class InputBranchesDef:
    on: str
    cases: dict[str, str]  # value -> step_id


@dataclass(frozen=True, slots=True)
class InputDef:
    title: str
    fields: list[InputFieldDef]
    branches: InputBranchesDef | None = None


@dataclass(frozen=True)
class SwitchDef:
    expr: str
    cases: dict[str, str] = field(default_factory=dict)
    default: str | None = None


@dataclass(frozen=True, slots=True)
class RunDef:
    key: str  # "wf:crm.customer.store"
    args: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StepDef:
    id: str
    input: InputDef | None = None
    run: RunDef | None = None
    switch: SwitchDef | None = None
    end: str | None = None
    next: str | None = None


@dataclass(frozen=True)
class WorkflowDef:
    id: str
    start: str
    steps: dict[str, StepDef]


@dataclass
class WorkflowError:
    code: str  # PERMISSION_DENIED, COMMAND_FAILED, ...
    message: str
    step_id: str
    command: str | None = None


class WorkflowStatus(StrEnum):
    PREPARED = "prepard"
    RUNNING = "running"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DONE = "done"
