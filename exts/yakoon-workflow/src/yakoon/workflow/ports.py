from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from yakoon.workflow.models.workflow import StepDef, WorkflowDef, WorkflowRuntime


class WorkflowService(Protocol):
    def runtime(self, session: Any) -> WorkflowRuntime: ...

    def enqueue_next(self, session: Any, batch_id: str) -> None: ...
    def complete_input_step(
        self,
        session,
        *,
        batch_id: str,
        step_id: str,
        values: Mapping[str, Any],
        ignore_none: bool = True,
    ) -> None: ...

    def complete_run_step(
        self, session: Any, *, batch_id: str, step_id: str
    ) -> None: ...

    def set_value(self, session: Any, batch_id: str, key: str, value: Any) -> None: ...
    def get_def(self, controller_id: str, command_key: str) -> WorkflowDef: ...
    def get_step(self, session: Any, batch_id: str, step_id: str) -> StepDef: ...

    def fail_batch(
        self,
        session,
        *,
        batch_id: str,
        code: str,
        message: str,
        command: str | None = None,
    ) -> None: ...
    def cancel_batch(self, session, *, batch_id: str) -> None: ...

    def start(
        self,
        session,
        controller_id: str,
        command_key: str,
        *,
        enqueue_first: bool = True,
    ) -> str: ...
    def start_with_values(
        self,
        session,
        controller_id: str,
        command_key: str,
        values: Mapping[str, Any],
        *,
        enqueue_first: bool = True,
        ignore_none: bool = True,
    ) -> str: ...
    def resume_with_values(
        self,
        session,
        batch_id: str,
        values: Mapping[str, Any],
        *,
        ignore_none: bool = True,
        enqueue_next: bool = True,
    ) -> None: ...


class WorkflowCompileService(Protocol):
    def compile(self, command_key: str, raw_text: str) -> WorkflowDef: ...
