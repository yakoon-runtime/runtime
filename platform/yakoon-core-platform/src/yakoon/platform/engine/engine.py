import time

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolverService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.capabilities.presenters.result import PresentResult
from yakoon.base.capabilities.workflow import WorkflowContextRequired
from yakoon.base.engine import CommandDispatch, DispatchInput
from yakoon.base.engine.flow import FlowCursor
from yakoon.base.engine.step import (
    FlowFinished,
    FlowState,
    InputRequired,
    SleepRequired,
    SleepUntilRequired,
    Step,
    TickResult,
)
from yakoon.base.runtime import (
    CmdNotFound,
    Command,
    ExecStep,
    Request,
    Session,
)
from yakoon.base.runtime.commands.command import CommandContext
from yakoon.base.runtime.controllers import Controller
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui import v_error

from .directories import CommandDirectory, ControllerDirectory


class CommandEngine:

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

    async def _find_matching_command(
        self, controller_id, request: Request
    ) -> tuple[Controller | None, type[Command] | None] | None:

        result: tuple[str, type[Command]] | None = self._commands.find(
            controller_id, request.command
        )
        if result and isinstance(result, tuple):
            controller_id, command = result
            return self._controllers.get(controller_id), command

    async def dispatch(self, session: Session, di: DispatchInput) -> Step | None:

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
            await session.emit(v_error("Kein aktiver Controller gesetzt."))
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
                raise CmdNotFound(request.command)

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
                raise PermissionError("Permission denied")

            session.execution.step(
                ExecStep.COMMAND_PREPARED,
                command=command_type.key,
                controller=resolved_controller.id,
            )

            session.flow = {
                "command_key": command_type.key,
                "controller_id": resolved_controller.id,
                "request": request.raw,
                "cursor": FlowCursor(command_type.run),
            }

        except CmdNotFound:
            await session.emit(
                v_error(f"{request.command}': command not found... use 'man'")
            )

        except PermissionError as exc:
            self.services.get(AuditLogService).security(
                session,
                "command",
                command_type.key if command_type else request.command,
            )
            await session.emit(v_error(str(exc)))

        except WorkflowContextRequired:
            await session.emit(
                v_error(
                    f"{request.command}': may only be executed from within a workflow.'"
                )
            )

        except Exception as exc:
            self.services.get(AuditLogService).error(exc, session)
            await session.emit(v_error("Ein interner Fehler ist aufgetreten."))

        finally:
            if command_type:
                command_type.context = None
            await controller.on_cleanup(session)

    def create_command(self, command_type: type, controller: Controller) -> Command:
        command = command_type()
        command.context = CommandContext(controller, "")
        return command

    async def tick(self, session: Session) -> TickResult:

        def now():
            return time.time()

        flow = session.flow
        if not flow:
            return TickResult(FlowState.FINISHED, None)

        cursor = flow["cursor"]
        command_key = flow["command_key"]
        controller_id = flow["controller_id"]
        request = Request(flow["request"])

        controller = self._controllers.get(controller_id)
        if not controller:
            raise RuntimeError(
                f"Resolved controller is None for command '{request.raw}'"
            )

        command_type = self._commands.get_type(controller_id, command_key)
        if not command_type:
            raise RuntimeError(
                f"Resolved command is None for input '{request.raw}' "
                f"(controller='{controller.id}')"
            )

        command = self.create_command(command_type, controller)

        # TODO: nur beim ersten Step
        # Pre-command hook
        # await controller.on_before_run_command(session, request, command)

        session.execution.step(
            ExecStep.COMMAND_RUNNING,
            command=command.key,
            controller=controller.id,
        )

        try:
            if "input" in flow:
                raw_values: dict = flow.pop("input", {})

                step = flow["last_step"]
                result_values = await step.resume(session, raw_values)

                value = PresentResult(result_values, {}, list(result_values.keys()))
                step = await cursor.send(value)
            else:
                step = await cursor.next(command, session, request)

            flow["last_step"] = step
        except StopAsyncIteration:
            session.flow = {}
            return TickResult(FlowState.FINISHED, FlowFinished())

        # Step ausführen
        outcome = await step.run(session, request)

        if isinstance(outcome, SleepRequired):
            flow["wake_at"] = now() + outcome.seconds
            return TickResult(FlowState.WAITING, None)

        if isinstance(outcome, SleepUntilRequired):
            flow["wake_at"] = outcome.timestamp
            return TickResult(FlowState.WAITING, None)

        # WAITING
        if isinstance(outcome, InputRequired):
            return TickResult(FlowState.WAITING, outcome)

        # FINISHED (explizit)
        if isinstance(outcome, FlowFinished):
            # Nur beim letzten Step
            await controller.on_after_run_command(session, request, command)

            session.flow = {}
            return TickResult(FlowState.FINISHED, outcome)

        # 🔵 RUNNING
        return TickResult(FlowState.RUNNING, outcome)
