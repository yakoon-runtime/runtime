from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolverService
from yakoon.base.capabilities.identity import Permission, PermissionService
from yakoon.base.capabilities.workflow import WorkflowContextRequired, WorkflowService
from yakoon.base.engine import CommandDispatch, DispatchInput
from yakoon.base.engine.flow import FlowCursor
from yakoon.base.engine.step import (
    FlowFinished,
    FlowState,
    InputRequired,
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
from yakoon.platform.ui import ViewSpecValidationError

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

            command = self.create_command(command_type, controller)

            session.execution.step(
                ExecStep.COMMAND_PREPARED,
                command=command_type.key,
                controller=resolved_controller.id,
            )

            # Pre-command hook
            await controller.on_before_run_command(session, request, command)
            await command.respond(session, request)

            session.execution.step(
                ExecStep.COMMAND_RUNNING,
                command=command.key,
                controller=controller.id,
            )

            session.flow = {
                "started": True,
                "finished": False,
                "waiting": False,
                "command_key": command_type.key,
                "controller_id": resolved_controller.id,
                "request": request.raw,
                "cursor": FlowCursor(command_type.flow),
                "ctx": {},
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

    async def tick(self, session: Session):

        failed = False
        command: Command | None = None

        flow = session.flow
        cursor = flow["cursor"]
        command_key = flow["command_key"]
        controller_id = flow["controller_id"]
        request = Request(flow["request"])

        # print("TICK", flow.get("ctx"))

        if not request.command:
            return

        controller = self._controllers.get(controller_id)
        if not controller:
            raise RuntimeError(f"Controller is None for command '{request.raw}'")

        command_type = self._commands.get_type(controller_id, command_key)
        if not command_type:
            raise RuntimeError(
                f"Command is None for input '{request.raw}' "
                f"(controller='{controller.id}')"
            )

        try:
            command = self.create_command(command_type, controller)

            # check permissions
            if not flow["started"]:
                perm_service = self.services.get(PermissionService)
                fq = Permission.fq_key(controller.id, command.key)
                if not perm_service.can_execute(session, fq):
                    raise PermissionError("Permission denied")
                flow["started"] = True

            try:
                step = await cursor.next(command, session, request)
            except StopAsyncIteration:
                flow["finished"] = True
                session.flow = {}
                return TickResult(FlowState.FINISHED, FlowFinished())

            outcome = await step.run(session, request)
            if isinstance(outcome, InputRequired):
                flow["waiting"] = True
                return TickResult(state=FlowState.WAITING, outcome=outcome)

            if isinstance(outcome, FlowFinished) and not flow.get("finished"):
                # Post-command hook
                await controller.on_after_run_command(session, request, command)
                flow["finished"] = True

                session.flow = {}
                session.execution.step(
                    ExecStep.COMMAND_SUCCESS,
                    command=command.key,
                    controller=controller.id,
                )
                return TickResult(FlowState.FINISHED, outcome)

            flow["waiting"] = False
            return TickResult(FlowState.RUNNING, outcome)

        except PermissionError as exc:
            failed = True

            # command may be None if permission fails early
            command_key = command.key if command else request.command
            self._services.get(AuditLogService).security(
                session, "command", command_key
            )
            await session.emit(v_error(str(exc)))
            # self.wf_failed(exc, command, session, di)

        except ValueError as exc:
            failed = True
            await session.emit(v_error(str(exc)))
            # self.wf_failed(exc, command, session, di)

        except ViewSpecValidationError as exc:
            self._services.get(AuditLogService).error(exc, session)
            await session.emit(
                v_error("Ein interner Konfigurationsfehler ist aufgetreten.")
            )

        except Exception as exc:
            failed = True
            self._services.get(AuditLogService).error(exc, session)
            await session.emit(v_error("Ein interner Fehler ist aufgetreten."))
            # self.wf_failed(exc, command, session, di)

        finally:

            if failed:
                session.execution.step(
                    ExecStep.COMMAND_FAILED,
                    command=command.key if command else None,
                    controller=controller.id if controller else None,
                )

            # if failed and di.batch_id:
            #    wf = self._services.get(WorkflowService)
            #    wf.cancel_batch(session, batch_id=di.batch_id)

            # Policy 2: cleanup the controller that executed this command
            # (NOT the current active controller after the command potentially
            # changed it)
            await controller.on_cleanup(session)

    def wf_failed(
        self,
        exc: Exception,
        command: Command | None,
        session: Session,
        di: DispatchInput,
    ) -> None:
        if di.batch_id and command:
            wf = self._services.get(WorkflowService)
            wf.fail_batch(
                session,
                batch_id=di.batch_id,
                code="",  # TODO code ist empty
                message=str(exc),
                command=command.key,
            )
