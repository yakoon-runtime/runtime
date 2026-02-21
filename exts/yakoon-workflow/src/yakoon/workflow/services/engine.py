from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from yakoon.base import ports as base_ports
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.resources.reference import resolve_resource
from yakoon.workflow import ports as wf_ports
from yakoon.workflow.models.workflow import (
    WorkflowDef,
    WorkflowError,
    WorkflowRuntime,
    WorkflowStatus,
)
from yakoon.workflow.runtime.compiler import compile_run_command


class WorkflowNotFound(KeyError):
    pass


class WorkflowService:

    def __init__(self, services: ServiceDirectory):
        self.services = services

    # ---- runtime access ----

    def runtime(self, session) -> WorkflowRuntime:
        meta = session._runtime.meta
        rt = meta.get("workflow")
        if rt is None:
            rt = WorkflowRuntime()
            meta["workflow"] = rt
        return rt

    # ---- loading (no caching) ----

    def get_def(self, controller_id: str, command_key: str) -> WorkflowDef:
        catalog = self.services.get(base_ports.ControllerCatalogService)
        info = catalog.get(controller_id)
        if not info:
            raise RuntimeError("ControllerInfo cannot be None.")

        resources = info.resources
        if not resources:
            raise RuntimeError("ControllerInfo has no Resources.")

        ref = resolve_resource(
            resources,
            i18n_root=resources.workflows,
            lang=None,
            key=command_key,
        )

        file_loader = self.services.get(base_ports.FileLoader)
        raw_text = file_loader.load_text(ref)
        if not raw_text:
            raise RuntimeError("Workflow definition not found.")

        compiler = self.services.get(wf_ports.WorkflowCompileService)
        wf = compiler.compile(command_key, raw_text)

        return wf

    # ---- orchestration (v1: prompt/run/end, linear next) ----

    def set_value(self, session, batch_id: str, key: str, value: Any) -> None:
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            raise RuntimeError(f"Unknown workflow batch: {batch_id}")
        batch.values[key] = value

    def start_with_values(
        self,
        session,
        controller_id: str,
        command_key: str,
        values: Mapping[str, Any],
        *,
        enqueue_first: bool = True,
        ignore_none: bool = True,
    ) -> str:
        """
        Convenience wrapper:
        - creates workflow batch
        - sets initial batch.values
        - enqueues first step (default)

        Args:
            enqueue_first:
                If True, enqueue the first step AFTER values were set.
                If False, caller may enqueue manually (rare).
            ignore_none:
                If True, keys with value None are not written into batch.values.
                This keeps 'missing' semantics intact.
        """
        batch_id = self.start(
            session,
            controller_id=controller_id,
            command_key=command_key,
            enqueue_first=False,
        )

        for k, v in values.items():
            if ignore_none and v is None:
                continue
            self.set_value(session, batch_id, k, v)

        if enqueue_first:
            self.enqueue_next(session, batch_id)

        return batch_id

    def start(
        self,
        session,
        controller_id: str,
        command_key: str,
        *,
        enqueue_first: bool = True,
    ) -> str:
        wf = self.get_def(controller_id, command_key)

        batch_id = uuid4().hex

        rt = self.runtime(session)
        batch = rt.ensure(batch_id, controller_id, command_key)
        batch.current_step = wf.start
        batch.pending_step = None
        batch.status = (
            WorkflowStatus.RUNNING if enqueue_first else WorkflowStatus.PREPARED
        )
        if enqueue_first:
            self.enqueue_next(session, batch_id)

        return batch_id

    def resume_with_values(
        self,
        session,
        batch_id: str,
        values: Mapping[str, Any],
        *,
        ignore_none: bool = True,
        enqueue_next: bool = True,
    ) -> None:
        """
        Convenience:
        - set/override multiple values in an existing workflow batch
        - then continue workflow by enqueuing the next step (default)

        Typical use:
        - GUI form submits multiple fields at once
        - a command collects several values and wants to continue

        wf.resume_with_values(session, batch_id, {
            "customer.first_name": first,
            "customer.last_name": last,
            "customer.email": email,
        })
        """
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            raise RuntimeError(f"Unknown workflow batch: {batch_id}")

        for k, v in values.items():
            if ignore_none and v is None:
                continue
            self.set_value(session, batch_id, k, v)

        if enqueue_next:
            self.enqueue_next(session, batch_id)

    def get_step(self, session, batch_id: str, step_id: str):
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch or not batch.controller_id or not batch.command_key:
            raise RuntimeError(f"Unknown workflow batch: {batch_id}")

        wf = self.get_def(batch.controller_id, batch.command_key)
        step = wf.steps.get(step_id)
        if not step:
            raise KeyError(
                f"Step not found: {batch.controller_id}:{batch.command_key}::{step_id}"
            )
        return step

    def enqueue_next(self, session, batch_id: str) -> None:
        rt, batch, wf, step = self._resolve_current_step(session, batch_id)
        if not batch:
            return

        self._ensure_running(batch)

        queue = self.services.get(base_ports.CommandQueueService)

        if step.end:
            self._enqueue_end(rt, batch_id, batch)
            return

        if step.input:
            self._enqueue_input(queue, session, batch_id, batch, step)
            return

        if step.switch:
            self._enqueue_switch(session, batch_id, batch, step)
            return

        if step.run:
            self._enqueue_run(queue, session, batch_id, batch, step)
            return

        raise ValueError(
            f"Invalid step '{batch.controller_id}:{batch.command_key}::{step.id}': "
            "neither input nor switch nor run nor end"
        )

    def _resolve_current_step(self, session, batch_id: str):
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch or not batch.controller_id or not batch.command_key:
            return rt, None, None, None

        wf = self.get_def(batch.controller_id, batch.command_key)
        step_id = batch.current_step or wf.start
        step = wf.steps.get(step_id)
        if not step:
            raise KeyError(
                f"Step not found: {batch.controller_id}:{batch.command_key}::{step_id}"
            )

        return rt, batch, wf, step

    def _ensure_running(self, batch) -> None:
        if batch.status == WorkflowStatus.PREPARED:
            batch.status = WorkflowStatus.RUNNING

    def _enqueue_end(self, rt: WorkflowRuntime, batch_id: str, batch) -> None:
        batch.status = WorkflowStatus.DONE
        rt.remove(batch_id)

    def _enqueue_input(self, queue, session, batch_id: str, batch, step) -> None:
        queue.enqueue_commands(
            session, [f"wf.input {batch_id} {step.id}"], batch_id=batch_id
        )
        batch.pending_step = step.id

    def _enqueue_switch(self, session, batch_id: str, batch, step) -> None:
        rendered = compile_run_command(
            step.switch.expr,
            batch.values,
            context=f"{batch.controller_id}:{batch.command_key}:{step.id}",
        ).strip()

        key = rendered.strip().lower()
        next_id = step.switch.cases.get(key) or step.switch.default
        if not next_id:
            raise RuntimeError(
                f"Switch step '{batch.controller_id}:{batch.command_key}::{step.id}': "
                f"no case for '{key}' and no default"
            )

        batch.current_step = next_id
        self.enqueue_next(session, batch_id)

    def _enqueue_run(self, queue, session, batch_id: str, batch, step) -> None:
        run_def = step.run
        ctx = f"{batch.controller_id}:{batch.command_key}:{step.id}"

        cmd = compile_run_command(run_def.key, batch.values, context=ctx)

        if run_def.args:
            rendered_args = [
                compile_run_command(arg, batch.values, context=ctx)
                for arg in run_def.args
            ]
            cmd = cmd + " " + " ".join(rendered_args)

        queue.enqueue_commands(
            session, [cmd, f"wf.next {batch_id} {step.id}"], batch_id=batch_id
        )

    def complete_input_step(
        self,
        session,
        *,
        batch_id: str,
        step_id: str,
        values: Mapping[str, Any],
        ignore_none: bool = True,
    ) -> None:
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            return

        step = self.get_step(session, batch_id, step_id)
        if not step.input:
            raise RuntimeError(f"Step {step_id} is not an input step")

        # commit values
        for k, v in values.items():
            if ignore_none and v is None:
                continue
            batch.values[k] = v

        batch.pending_step = None

        # branches
        next_id = step.next
        br = step.input.branches
        if br is not None:
            raw = batch.values.get(br.on)
            key = "" if raw is None else str(raw).strip().lower()
            next_id = br.cases.get(key)
            if not next_id:
                raise RuntimeError(
                    f"Input step '{step.id}': branches has no target for '{key}'"
                )

        if not next_id:
            rt.remove(batch_id)
            return

        batch.current_step = next_id
        self.enqueue_next(session, batch_id)

    def complete_run_step(self, session, *, batch_id: str, step_id: str) -> None:
        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            return

        step = self.get_step(session, batch_id, step_id)
        if not step.run:
            raise RuntimeError(f"Step {step_id} is not a run step")

        if not step.next:
            rt.remove(batch_id)
            return

        batch.current_step = step.next
        self.enqueue_next(session, batch_id)

    def fail_batch(
        self,
        session,
        *,
        batch_id: str,
        code: str,
        message: str,
        command: str | None = None,
    ) -> None:

        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            return

        step_id = batch.pending_step or batch.current_step
        batch.status = WorkflowStatus.FAILED
        batch.error = WorkflowError(
            code=code, message=message, step_id=step_id, command=command
        )

    def cancel_batch(self, session, *, batch_id: str) -> None:

        rt = self.runtime(session)
        batch = rt.get(batch_id)
        if not batch:
            return

        batch.status = WorkflowStatus.CANCELLED
        batch.error = None

        queue = self.services.get(base_ports.CommandQueueService)
        queue.cancel_batch(session, batch_id)
