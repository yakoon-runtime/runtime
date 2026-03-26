import time
from uuid import uuid4

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolverService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.engine import (
    CommandDispatch,
    DispatchInput,
)
from yakoon.base.runtime.commands import (
    Command,
    Request,
)
from yakoon.base.runtime.commands.context import CommandContext
from yakoon.base.runtime.controllers import Controller
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.runtime.steps import (
    BLOCKING_STEPS,
    ClearFocus,
    Effect,
    Emit,
    Outcome,
    SetFocus,
    Stop,
    YieldToScheduler,
)
from yakoon.base.runtime.steps.context import StepContext
from yakoon.base.runtime.steps.effects import AutoFocus
from yakoon.base.ui import v_error_system
from yakoon.platform.runtime import CommandNotFound, PermissionDenied
from yakoon.platform.runtime.error import CriticalError
from yakoon.platform.runtime.flow import (
    Flow,
    FlowCursor,
    FlowKind,
    FlowState,
)
from yakoon.platform.runtime.sessions import Session

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
            await session.emit(v_error_system("Kein aktiver Controller gesetzt."))
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

    async def tick_flow(self, flow: Flow, session: Session) -> Outcome | None:

        cursor = flow.cursor
        request = Request(flow.request)

        context = StepContext(
            session=session,
            request=request,
            services=self.services,
        )

        controller = self._controllers.get(flow.controller_id)
        if not controller:
            raise RuntimeError("Controller not found")

        command_type = self._commands.get_type(flow.controller_id, flow.command_key)
        if not command_type:
            raise RuntimeError("Command not found")

        command = self._create_command(command_type, controller, session)

        steps = 0
        start = time.time()

        max_steps, max_time = self._get_inline_budget(flow)

        try:
            session._runtime_flow_id = flow.id  # type: ignore

            while True:

                # --------------------------------------------------
                # 1. nächstes Item holen
                # --------------------------------------------------
                item = await self._next_step(flow, session, command, request)
                if item is None:
                    return None

                # --------------------------------------------------
                # 2. ausführen (zentral!)
                # --------------------------------------------------
                outcome = await self._execute_item(item, flow, context)

                # --------------------------------------------------
                # 3. VALUE LOOP
                # --------------------------------------------------
                while outcome.value is not None:

                    value = outcome.value
                    outcome.value = None

                    item = await cursor.send(value)

                    outcome = await self._execute_item(item, flow, context)

                # --------------------------------------------------
                # 4. Safety
                # --------------------------------------------------
                if not isinstance(outcome, Outcome):
                    raise RuntimeError(f"Invalid step result: {type(outcome)}")

                # --------------------------------------------------
                # 5. Effects
                # --------------------------------------------------
                if outcome.effects:
                    await self._apply_effects(outcome.effects, context.session, flow)

                # --------------------------------------------------
                # 6. Control (Scheduler)
                # --------------------------------------------------
                control = outcome.control

                if control is not None:
                    if isinstance(control, BLOCKING_STEPS):
                        return Outcome(control=control)

                # --------------------------------------------------
                # 7. Budget / Fairness
                # --------------------------------------------------
                steps += 1

                if steps >= max_steps:
                    return Outcome(control=YieldToScheduler())

                if time.time() - start > max_time:
                    return Outcome(control=YieldToScheduler())

        except StopAsyncIteration:
            return Outcome(control=Stop())

        finally:
            session._runtime_flow_id = None  # type: ignore

    # ----------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------

    def _get_inline_budget(self, flow: Flow):
        base_steps = 20
        base_time = 0.005
        if flow.kind == FlowKind.SYSTEM:
            return base_steps * 3, base_time * 2
        return base_steps, base_time

    async def _execute_item(self, item, flow, context) -> Outcome:

        # Generator = First-Class
        if hasattr(item, "__aiter__"):
            return await self._run_generator(item, flow, context)

        if isinstance(item, Outcome):
            return item

        if isinstance(item, tuple):
            step, event = item
            return await step.resume(flow, event, context)

        # normaler Step
        return await item.run(flow, context)

    async def _run_generator(self, gen, flow, context) -> Outcome:

        send_value = None

        while True:
            try:
                if send_value is None:
                    item = await anext(gen)
                else:
                    item = await gen.asend(send_value)
                    send_value = None

            except StopAsyncIteration:
                return Outcome()

            outcome = await self._execute_item(item, flow, context)

            # ----------------------------------
            # VALUE → zurück in Generator
            # ----------------------------------
            if outcome.value is not None:
                send_value = outcome.value
                continue

            # ----------------------------------
            # EFFECTS → sofort anwenden
            # ----------------------------------
            if outcome.effects:
                await self._apply_effects(outcome.effects, context.session, flow)

            # ----------------------------------
            # CONTROL → Scheduler übergeben
            # ----------------------------------
            if outcome.control is not None:
                return outcome

            # ----------------------------------
            # sonst: weiterlaufen
            # ----------------------------------
            continue

    async def _apply_effects(self, effects: list[Effect], session: Session, flow):

        for effect in effects:

            if isinstance(effect, Emit):
                await session.emit(effect.view)

            elif isinstance(effect, AutoFocus):
                session.set_focus(flow.id)

            elif isinstance(effect, SetFocus):
                session.set_focus(effect.flow_id)

            elif isinstance(effect, ClearFocus):
                session.set_focus(None)

    async def _next_step(
        self, flow: Flow, session: Session, command: Command, request: Request
    ):

        # ----------------------------------
        # Resume: Input direkt zurück in Generator
        # ----------------------------------
        if flow.state == FlowState.WAITING_INPUT:
            if not flow.input_queue:
                return None

            _, event = flow.input_queue.popleft()
            value = await flow.cursor.send(event)
            return value

        # ----------------------------------
        # Normal: nächstes Item vom Generator
        # ----------------------------------
        return await flow.cursor.next(command, request)

    def _create_command(
        self, command_type: type, controller: Controller, session: Session
    ) -> Command:
        command = command_type()
        command.context = CommandContext(session, controller)
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
