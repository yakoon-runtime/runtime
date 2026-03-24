import time
from uuid import uuid4

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolverService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.engine import (
    CommandDispatch,
    DispatchInput,
)
from yakoon.base.runtime import (
    Command,
    CommandContext,
    ExecStep,
    Request,
    Session,
)
from yakoon.base.runtime.controllers import Controller
from yakoon.base.runtime.flow import (
    Flow,
    FlowCursor,
    FlowKind,
    FlowState,
)
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.runtime.steps import (
    BLOCKING_STEPS,
    ClearFocus,
    Control,
    Effect,
    Emit,
    InputStep,
    Outcome,
    SetFocus,
    Stop,
    YieldToScheduler,
)
from yakoon.base.ui import v_error_system
from yakoon.platform.runtime import CommandNotFound, PermissionDenied, PlatformError

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

        session.execution.reset()
        session.execution.step(ExecStep.EXECUTION_START)
        if not isinstance(di, CommandDispatch):
            return None

        request = Request(di.text)
        if not request.command:
            return None

        session.execution.step(
            ExecStep.COMMAND_RECEIVED,
            command=request.raw,
        )

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

            session.execution.step(
                ExecStep.COMMAND_RESOLVED,
                command=command_type.key,
                controller=resolved_controller.id,
            )

            # Permission check
            perm_service = self.services.get(PermissionService)
            fq = Permission.fq_key(resolved_controller.id, command_type.key)
            if not perm_service.can_execute(session, fq):
                raise PermissionDenied()

            session.execution.step(
                ExecStep.COMMAND_PREPARED,
                command=command_type.key,
                controller=resolved_controller.id,
            )

            flow = Flow(
                uuid4().hex,
                command_type.key,
                resolved_controller.id,
                request.raw,
                FlowCursor(command_type.run),
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
            raise PlatformError(
                "Ein interner Fehler ist aufgetreten.",
                "internal_error",
            ) from exc

        finally:
            if command_type:
                command_type.context = None
            await controller.on_cleanup(session)

    async def tick_flow(self, flow: Flow, session: Session) -> Control | None:

        cursor = flow.cursor
        request = Request(flow.request)

        controller = self._controllers.get(flow.controller_id)
        if not controller:
            raise RuntimeError("Controller not found")

        command_type = self._commands.get_type(flow.controller_id, flow.command_key)
        if not command_type:
            raise RuntimeError("Command not found")

        command = self._create_command(command_type, controller)

        steps = 0
        start = time.time()

        max_steps, max_time = self._get_inline_budget(flow)

        try:
            session._runtime_flow_id = flow.id

            while True:

                # --------------------------------------------------
                # 1. Step holen (KEINE Interpretation!)
                # --------------------------------------------------
                step = await self._next_step(flow, session, command, request)
                if step is None:
                    return None

                # --------------------------------------------------
                # 2. Step → Outcome
                # --------------------------------------------------
                if isinstance(step, Outcome):
                    outcome = step
                else:
                    flow.last_step = step
                    outcome = await step.run(session, flow, request)

                # --------------------------------------------------
                # 3. InputEvent + value
                # --------------------------------------------------
                while outcome.value is not None:

                    item = await cursor.send(outcome.value)
                    outcome.value = None

                    if isinstance(item, Outcome):
                        outcome = item
                        continue

                    # muss Step sein
                    flow.last_step = item
                    outcome = await item.run(session, flow, request)

                # Safety
                if not isinstance(outcome, Outcome):
                    raise RuntimeError(f"Invalid step result: {type(outcome)}")

                # --------------------------------------------------
                # 4. Effects ausführen
                # --------------------------------------------------
                await self._apply_effects(outcome.effects, session)

                # --------------------------------------------------
                # 5. Control → Scheduler
                # --------------------------------------------------
                control = outcome.control

                if control is not None:
                    if isinstance(control, BLOCKING_STEPS):
                        return control

                # --------------------------------------------------
                # 6. Budget / Fairness
                # --------------------------------------------------
                steps += 1

                if steps >= max_steps:
                    return YieldToScheduler()

                if time.time() - start > max_time:
                    return YieldToScheduler()

        except StopAsyncIteration:
            return Stop()

        finally:
            session._runtime_flow_id = None

    # ----------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------

    def _get_inline_budget(self, flow: Flow):
        base_steps = 20
        base_time = 0.005
        if flow.kind == FlowKind.SYSTEM:
            return base_steps * 3, base_time * 2
        return base_steps, base_time

    async def _apply_effects(self, effects: list[Effect], session: Session):

        for effect in effects:

            if isinstance(effect, Emit):
                await session.emit(effect.view)

            elif isinstance(effect, SetFocus):
                session.set_focus(effect.flow_id)

            elif isinstance(effect, ClearFocus):
                session.set_focus(None)

    async def _next_step(
        self, flow: Flow, session: Session, command: Command, request: Request
    ):
        # Resume (nur für InputStep)
        if flow.state == FlowState.WAITING_INPUT:

            if not flow.input_queue:
                return None

            step = flow.last_step
            if not step:
                raise RuntimeError("Missing last_step for resume")

            if isinstance(step, InputStep):
                _, event = flow.input_queue.popleft()
                return await step.resume(session, flow, event)
            else:
                event = flow.pop_event()
                item = await flow.cursor.send(event)
                return item

        # normaler Flow
        return await flow.cursor.next(command, session, request)

    def _create_command(self, command_type: type, controller: Controller) -> Command:
        command = command_type()
        command.context = CommandContext(controller, "")
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
