from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

from yakoon.base.application.application import Application
from yakoon.base.capabilities.identity import Permission
from yakoon.base.commands import Command, Request
from yakoon.base.controllers.controller import Controller
from yakoon.base.flow.primitives import (
    AutoFocus,
    AwaitEvent,
    ClearFocus,
    Continue,
    Effect,
    EmitEvent,
    EmitView,
    Outcome,
    SetFocus,
    Stop,
)
from yakoon.base.projection.model.model import Projection
from yakoon.base.runtime import InputEvent
from yakoon.base.runtime.input.context import InputContext
from yakoon.platform.flow import Flow, FlowCursor, FlowKind
from yakoon.platform.runtime import (
    CommandNotFound,
    CriticalError,
    PermissionDenied,
    Session,
)

from .errors import system_error_projection


class CommandEngine:

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        on_match_command: OnMatchCommand,
        on_parse_input: OnParseInput,
        on_authorize: OnAuthorize,
        on_projection: OnProjection,
        on_audit_security: OnAuditSecurity,
        on_create_command: OnCreateCommand,
        on_get_app: OnGetApp,
        on_get_shell_app: OnGetShellApp,
    ):
        self.on_match_command = on_match_command
        self.on_parse_input = on_parse_input
        self.on_authorize = on_authorize
        self.on_projection = on_projection
        self.on_audit_security = on_audit_security
        self.on_get_app = on_get_app
        self.on_get_shell_app = on_get_shell_app
        self.on_create_command = on_create_command

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def dispatch(self, session: Session, event: InputEvent) -> Flow | None:

        # session.execution.reset()
        # session.execution.step(ExecStep.EXECUTION_START)
        event, pipeline_commands = self.on_parse_input(event=event)
        if not event or not event.command:
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RECEIVED,
        #    command=request.raw,
        # )

        # Active app sicherstellen
        app_id = session.get_active_app()
        if not app_id:
            shell = self.on_get_shell_app()
            if not shell:
                raise RuntimeError("dispatch() found no shell application")
            session.set_active_app(shell.id)
            app_id = shell.id

        app = self.on_get_app(app_id=app_id)
        if not app:
            await self.on_projection(
                session=session,
                projection=system_error_projection(
                    "dispatch() found no active application"
                ),
                ctx=event.context,
            )
            return None

        command_type: type[Command] | None = None

        try:

            # Hook vor resolve
            # await application.on_before_resolve(session)

            # Command finden
            result = self.on_match_command(
                app_id=app.id,
                command_key=event.command,
            )
            if not result:
                raise CommandNotFound(event.command)

            # if not result:
            #    resolver = self.container.get(LookupResolver)
            #    resolved = await resolver.resolve(session, event)
            #    if resolved:
            #        result = await self._find_matching_command(controller_id, event)

            app_id, controller_type, command_type = result

            # session.execution.step(
            #    ExecStep.COMMAND_RESOLVED,
            #    command=command_type.key,
            #    controller=resolved_controller.id,
            # )

            # Permission check
            fq = Permission.fq_key(app_id, command_type.key)
            if not self.on_authorize(session=session, perm_key=fq):
                raise PermissionDenied()

            # session.execution.step(
            #    ExecStep.COMMAND_PREPARED,
            #    command=command_type.key,
            #    controller=resolved_controller.id,
            # )

            command = self.on_create_command(
                session=session,
                controller=controller_type,
                command=command_type,
            )

            flow = Flow(
                id=uuid4().hex,
                app_id=app_id,
                command=command,
                pipeline=pipeline_commands,
                event=event,
                cursor=FlowCursor(),
                kind=self.DEFAULT_FLOW_KIND,
            )

            session.add_flow(flow)
            return flow

        except CommandNotFound:
            raise

        except PermissionDenied:
            self.on_audit_security(
                session=session,
                obj="command",
                action=command_type.key if command_type else event.command,
            )
            raise

        except Exception as exc:
            raise CriticalError(
                "Ein interner Fehler ist aufgetreten.",
                "internal_error",
            ) from exc

    async def step_flow(self, flow: Flow, session: Session) -> Outcome | None:

        cursor = flow.cursor
        command = flow.command

        try:
            session._runtime_flow_id = flow.id  # type: ignore

            # ----------------------------------
            # 21. NORMAL STEP
            # ----------------------------------
            item = await self._next_step(flow, command, flow.event)
            if item is None:
                return None

            if isinstance(item, InputEvent):
                try:
                    item = await cursor.send(item)
                except StopAsyncIteration:
                    cursor.pop()
                    if not cursor.has_stack():
                        return Outcome(control=Stop())
                    return None

            # ----------------------------------
            # 2. SUBGENERATOR (SUBFLOW / CALL)
            # ----------------------------------
            if inspect.isasyncgen(item):
                cursor.push(item)
                return None

            # ----------------------------------
            # 3. OUTCOME direkt
            # ----------------------------------
            if isinstance(item, Outcome):
                outcome = item
            else:
                outcome = await item.run(flow)

            # ----------------------------------
            # 3.1 OUTCOME value
            # ----------------------------------
            if outcome.value is not None:
                if flow.pipeline:
                    outcome.control = Continue(outcome.value)
                else:
                    if not outcome.effects:
                        outcome.effects = [EmitView(outcome.value)]
                        pass

            # ----------------------------------
            # 4. EFFECTS
            # ----------------------------------
            if outcome.effects:
                await self._apply_effects(outcome.effects, session, flow)

            # ----------------------------------
            # 5. CONTROL (Scheduler übernimmt)
            # ----------------------------------
            if outcome.control is not None:
                return outcome

            # ----------------------------------
            # 6. Kein Ergebnis → nächster Step später
            # ----------------------------------
            return None

        except StopAsyncIteration:
            # aktueller Generator ist fertig
            cursor.pop()

            if not cursor.has_stack():
                return Outcome(control=Stop())

            return None

        finally:
            session._runtime_flow_id = None  # type: ignore

    # ----------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------

    async def _apply_effects(
        self, effects: Sequence[Effect], session: Session, flow: Flow
    ):

        for effect in effects:

            if isinstance(effect, EmitView):
                await self.on_projection(
                    session=session,
                    projection=effect.view,
                    ctx=flow.event.context,
                    job_id=flow.id,
                )

            elif isinstance(effect, AutoFocus):
                session.set_interaction(flow.id)

            elif isinstance(effect, EmitEvent):
                flow.inbox[effect.channel].append(effect.event)

            elif isinstance(effect, SetFocus):
                session.set_interaction(effect.flow_id)

            elif isinstance(effect, ClearFocus):
                session.set_interaction(None)

    async def _next_step(self, flow: Flow, command, event: InputEvent):

        # ----------------------------------
        # Resume: Input / Event
        # ----------------------------------
        if isinstance(flow.control, AwaitEvent):

            channel = flow.control.channel

            next_event = flow.pop_event(channel)
            if next_event is None:
                return None

            flow.control = None
            return next_event

        # ----------------------------------
        # NEXT
        # ----------------------------------
        request = Request(event.command, event.tokens, event.payload)
        return await flow.cursor.next(command, request)


# ----------------------------------
# PORTS
# ----------------------------------


class OnMatchCommand(Protocol):
    def __call__(
        self, *, app_id: str, command_key: str
    ) -> tuple[str, type[Controller], type[Command]] | None: ...


class OnParseInput(Protocol):
    def __call__(self, *, event: InputEvent) -> tuple[InputEvent, list[str]]: ...


class OnAuthorize(Protocol):
    def __call__(self, *, session, perm_key: str) -> bool: ...


class OnProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...


class OnAuditSecurity(Protocol):
    def __call__(self, *, session, obj, action) -> None: ...


class OnGetApp(Protocol):
    def __call__(self, *, app_id: str) -> Application: ...


class OnGetShellApp(Protocol):
    def __call__(self) -> Application: ...


class OnCreateCommand(Protocol):
    def __call__(
        self, session: Session, controller: type[Controller], command: type[Command]
    ) -> Command: ...


class OnContinuePipeline(Protocol):
    async def __call__(self, session: Session, event: InputEvent) -> None: ...
