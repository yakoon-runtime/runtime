from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowContextRequired(Exception):
    pass


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


@dataclass
class WorkflowBatch:
    batch_id: str
    controller_id: str  # | None = None
    command_key: str  # | None = None

    values: dict[str, Any] = field(default_factory=dict)

    current_step: str | None = None
    pending_step: str | None = None

    status: WorkflowStatus = WorkflowStatus.RUNNING
    error: WorkflowError | None = None


@dataclass
class WorkflowRuntime:

    batches: dict[str, WorkflowBatch] = field(default_factory=dict)

    def get(self, batch_id: str) -> WorkflowBatch | None:
        return self.batches.get(batch_id)

    def ensure(
        self, batch_id: str, controller_id: str, command_key: str
    ) -> WorkflowBatch:
        b = self.batches.get(batch_id)
        if b is None:
            b = WorkflowBatch(
                batch_id=batch_id, controller_id=controller_id, command_key=command_key
            )
            self.batches[batch_id] = b
        return b

    def remove(self, batch_id: str) -> None:
        self.batches.pop(batch_id, None)
