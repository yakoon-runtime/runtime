import inspect
from uuid import uuid4

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.commands import Command, Request
from yakoon.base.commands.context import CommandContext
from yakoon.base.flow.primitives import (
    AutoFocus,
    AwaitEvent,
    ClearFocus,
    Effect,
    EmitEvent,
    EmitView,
    Outcome,
    SetFocus,
    Stop,
)
from yakoon.base.projection.transfer import Output
from yakoon.base.runtime import InputEvent
from yakoon.platform.catalogs import AppQueryBuilder
from yakoon.platform.flow import Flow, FlowCursor, FlowKind
from yakoon.platform.runtime import (
    CommandNotFound,
    CriticalError,
    PermissionDenied,
    Session,
)

from .errors import system_error_projection
from .resolver import CommandResolver


class CommandEngine:

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        apps: AppQueryBuilder,
        resolver: CommandResolver,
        permissions: PermissionService,
        auditlogs: AuditLogService,
        output: Output,
    ):
        self._apps = apps
        self._resolver = resolver
        self._permissions = permissions
        self._auditlogs = auditlogs
        self._output = output

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def dispatch(self, session: Session, event: InputEvent) -> None:

        # session.execution.reset()
        # session.execution.step(ExecStep.EXECUTION_START)
        if not event.command:
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RECEIVED,
        #    command=request.raw,
        # )

        # Active app sicherstellen
        app_id = session.get_active_app()
        if not app_id:
            shell = self._apps.shell()
            if not shell:
                raise RuntimeError("dispatch() found no shell application")
            session.set_active_app(shell.id)
            app_id = shell.id

        app = self._apps.get(app_id)
        if not app:
            await self._output.send_projection(
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
            result = self._resolver.resolve(app.id, event.command)
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
            if not self._permissions.can_execute(session, fq):
                raise PermissionDenied()

            # session.execution.step(
            #    ExecStep.COMMAND_PREPARED,
            #    command=command_type.key,
            #    controller=resolved_controller.id,
            # )

            flow = Flow(
                id=uuid4().hex,
                app_id=app_id,
                command_type=command_type,
                controller_type=controller_type,
                event=event,
                cursor=FlowCursor(),
                kind=self.DEFAULT_FLOW_KIND,
            )
            session.add_flow(flow)

        except CommandNotFound:
            raise

        except PermissionDenied:
            self._auditlogs.security(
                session,
                "command",
                command_type.key if command_type else event.command,
            )
            raise

        except Exception as exc:
            raise CriticalError(
                "Ein interner Fehler ist aufgetreten.",
                "internal_error",
            ) from exc

    async def step_flow(self, flow: Flow, session: Session) -> Outcome | None:

        cursor = flow.cursor

        command = flow.command_type()
        controller = flow.controller_type()
        command.ctx = CommandContext(session, controller)

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

    async def _apply_effects(self, effects: list[Effect], session: Session, flow: Flow):

        for effect in effects:

            if isinstance(effect, EmitView):
                await self._output.send_projection(
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
        request = Request(event.command, event.tokens)
        return await flow.cursor.next(command, request)
