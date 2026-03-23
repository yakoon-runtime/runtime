from yakoon.base.runtime import (
    Command,
    CommandFlow,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
    Session,
)
from yakoon.base.runtime.commands import Advance
from yakoon.base.ui.builder import v_text


class CmdJobs(Command):

    key = "jobs"

    kind = CommandKind.BUILTIN
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, session: Session, request: Request) -> CommandFlow:

        action = request.arg(0)

        if not action:
            await self._list_jobs(session)
            yield Advance()
            return

        if action == "stop":
            await self._stop_job(session, request)
            yield Advance()
            return

        if action == "use":
            await self._use_job(session, request)
            yield Advance()
            return

        await session.emit(v_text(f"Unbekannte Aktion: {action}"))
        yield Advance()

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _enumerate_flows(self, session: Session):
        flows = [f for f in session.flows() if f.command_key != self.key]
        return list(enumerate(flows, start=1))

    def _get_flow_by_index(self, session: Session, request: Request):
        try:
            index = int(request.arg(1))
        except (TypeError, ValueError):
            return None, None

        indexed = self._enumerate_flows(session)

        for i, flow in indexed:
            if i == index:
                return flow, index

        return None, index

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    async def _list_jobs(self, session: Session):

        indexed = self._enumerate_flows(session)

        if not indexed:
            await session.emit(v_text("Keine Jobs aktiv."))
            return

        await session.emit(v_text("Aktive Jobs:\n"))

        focused = session.focused_flow

        for i, f in indexed:
            label = getattr(f, "label", f.command_key)
            state = f.state.name
            marker = " *" if focused and focused.id == f.id else ""

            await session.emit(v_text(f"[{i}] {label} - {state}{marker}\n"))

    async def _stop_job(self, session: Session, request: Request):

        flow, index = self._get_flow_by_index(session, request)

        if not flow:
            await session.emit(v_text(f"Job {index} nicht gefunden"))
            return

        session.del_flow(flow)

        await session.emit(v_text(f"Job {index} gestoppt"))

    async def _use_job(self, session: Session, request: Request):

        flow, index = self._get_flow_by_index(session, request)

        if not flow:
            await session.emit(v_text(f"Job {index} nicht gefunden"))
            return

        session.set_focus(flow.id)

        await session.emit(v_text(f"Fokus auf Job {index} gesetzt"))
