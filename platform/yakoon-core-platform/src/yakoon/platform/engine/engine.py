import inspect
from uuid import uuid4

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolverService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.commands import Command, Request
from yakoon.base.commands.context import CommandContext
from yakoon.base.controllers import Controller
from yakoon.base.dispatch import CommandDispatch, DispatchInput
from yakoon.base.flow.primitives import (
    AutoFocus,
    AwaitEvent,
    AwaitInput,
    ClearFocus,
    Effect,
    EmitEvent,
    EmitView,
    Outcome,
    SetFocus,
    Stop,
)
from yakoon.base.presentation import OutputStream, v_error_system
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.platform.flow import Flow, FlowCursor, FlowKind
from yakoon.platform.runtime import (
    CommandNotFound,
    CriticalError,
    PermissionDenied,
    Session,
)

from .directories import CommandDirectory, ControllerDirectory


class CommandEngine:

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        controllers: ControllerDirectory,
        services: ServiceDirectory,
        commands: CommandDirectory,
    ):
        self._controllers = controllers
        self._services = services
        self._commands = commands
        self._output = services.get(OutputStream)

    @property
    def services(self) -> ServiceDirectory:
        return self._services

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def dispatch(self, session: Session, di: DispatchInput) -> None:

        # session.execution.reset()
        # session.execution.step(ExecStep.EXECUTION_START)
        if not isinstance(di, CommandDispatch):
            return None

        request = Request(di.text)
        if not request.command:
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RECEIVED,
        #    command=request.raw,
        # )

        # Active controller sicherstellen
        controller_id = session.get_active_controller()
        if not controller_id:
            shell = self._controllers.find_shell()
            if not shell:
                raise RuntimeError("Shell was not found.")
            session.set_active_controller(shell.id)
            controller_id = shell.id

        controller = self._controllers.get(controller_id)
        if not controller:
            await self._output.send_view(
                session, v_error_system("Kein aktiver Controller gesetzt.")
            )
            return None

        command_type: type[Command] | None = None

        try:

            # Hook vor resolve
            await controller.on_before_resolve(session)

            # Command finden
            result = await self._find_matching_command(controller_id, request)
            if not result:
                resolver = self.services.get(LookupResolverService)
                resolved = await resolver.resolve(session, request)
                if resolved:
                    request = Request(resolved)
                    result = await self._find_matching_command(controller_id, request)

            if not result:
                raise CommandNotFound(request.command)

            resolved_controller, command_type = result
            if not resolved_controller:
                raise RuntimeError(
                    f"Resolved controller is None for command '{request.raw}'"
                )

            if not command_type:
                raise RuntimeError(
                    f"Resolved command is None for input '{request.raw}' "
                    f"(controller='{resolved_controller.id}')"
                )

            # session.execution.step(
            #    ExecStep.COMMAND_RESOLVED,
            #    command=command_type.key,
            #    controller=resolved_controller.id,
            # )

            # Permission check
            perm_service = self.services.get(PermissionService)
            fq = Permission.fq_key(resolved_controller.id, command_type.key)
            if not perm_service.can_execute(session, fq):
                raise PermissionDenied()

            # session.execution.step(
            #    ExecStep.COMMAND_PREPARED,
            #    command=command_type.key,
            #    controller=resolved_controller.id,
            # )

            flow = Flow(
                uuid4().hex,
                command_type.key,
                resolved_controller.id,
                request.raw,
                FlowCursor(),
                kind=self._resolve_flow_kind(request),
            )
            session.add_flow(flow)

        except CommandNotFound:
            raise

        except PermissionDenied:
            self.services.get(AuditLogService).security(
                session,
                "command",
                command_type.key if command_type else request.command,
            )
            raise

        except Exception as exc:
            raise CriticalError(
                "Ein interner Fehler ist aufgetreten.",
                "internal_error",
            ) from exc

    async def step_flow(self, flow: Flow, session: Session) -> Outcome | None:

        cursor = flow.cursor
        request = Request(flow.request)

        controller = self._controllers.get(flow.controller_id)
        if not controller:
            raise RuntimeError("Controller not found")

        command_type = self._commands.get_type(flow.controller_id, flow.command_key)
        if not command_type:
            raise RuntimeError("Command not found")

        command = self._create_command(command_type, controller, session)

        try:
            session._runtime_flow_id = flow.id  # type: ignore

            # ----------------------------------
            # 21. NORMAL STEP
            # ----------------------------------
            item = await self._next_step(flow, session, command, request)

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

    async def _apply_effects(self, effects: list[Effect], session: Session, flow):

        for effect in effects:

            if isinstance(effect, EmitView):
                await self._output.send_view(session, effect.view)

            elif isinstance(effect, AutoFocus):
                session.set_interaction(flow.id)

            elif isinstance(effect, EmitEvent):
                flow.inbox[effect.channel].append(effect.event)

            elif isinstance(effect, SetFocus):
                session.set_interaction(effect.flow_id)

            elif isinstance(effect, ClearFocus):
                session.set_interaction(None)

    async def _next_step(self, flow: Flow, session, command, request):

        # ----------------------------------
        # Resume: Input / Event
        # ----------------------------------
        if isinstance(flow.control, AwaitInput):

            channel = "default"

            event = flow.pop_event(channel)
            if event is None:
                return None

            flow.control = None
            return event

        # ----------------------------------
        # Resume: Input / Event
        # ----------------------------------
        if isinstance(flow.control, AwaitEvent):

            channel = flow.control.channel

            event = flow.pop_event(channel)
            if event is None:
                return None

            flow.control = None
            return event

        # ----------------------------------
        # NEXT
        # ----------------------------------
        return await flow.cursor.next(command, request)

    def _create_command(
        self, command_type: type[Command], controller: Controller, session: Session
    ) -> Command:
        command = command_type()
        command.ctx = CommandContext(session, controller)
        return command

    async def _find_matching_command(
        self, controller_id, request: Request
    ) -> tuple[Controller | None, type[Command] | None] | None:

        result: tuple[str, type[Command]] | None = self._commands.find(
            controller_id, request.command
        )
        if result and isinstance(result, tuple):
            controller_id, command = result
            return self._controllers.get(controller_id), command

    def _resolve_flow_kind(self, request: Request):
        """
        usage:
        --job background
        """
        job = request.option("job")
        if not job:
            return self.DEFAULT_FLOW_KIND

        job = job.lower()
        if job in FlowKind._value2member_map_:
            return FlowKind(job)

        return self.DEFAULT_FLOW_KIND
