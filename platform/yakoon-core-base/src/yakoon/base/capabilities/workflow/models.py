from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import WorkflowError, WorkflowStatus


class WorkflowNotFound(KeyError):
    pass


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
