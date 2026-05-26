from y5n.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
)
from y5n.base.flow.patterns import write_text


class CmdJobs(Command):

    key = "jobs"

    kind = CommandKind.BUILTIN
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, request: Request):

        action = request.arg(0)

        if not action:
            yield self._list_jobs()

        elif action == "stop":
            yield self._stop_job(request)

        elif action == "use":
            yield self._use_job(request)

        else:
            yield write_text(f"Unbekannte Aktion: {action}")

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _enumerate_flows(self):
        session = self.ctx.session
        flows = [f for f in session.flows() if f.command_key != self.key]
        return list(enumerate(flows, start=1))

    def _get_flow_by_index(self, request: Request):
        try:
            index = int(request.arg(1))
        except (TypeError, ValueError):
            return None, None

        indexed = self._enumerate_flows()

        for i, flow in indexed:
            if i == index:
                return flow, index

        return None, index

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    async def _list_jobs(self):

        indexed = self._enumerate_flows()

        if not indexed:
            yield write_text("Keine Jobs aktiv.")
            return

        yield write_text("Aktive Jobs:\n")

        focused = self.ctx.session.interaction_flow
        for i, f in indexed:
            label = f.label() if hasattr(f, "label") else f.command_key
            state = f.control.label(f) if f.control else "run"
            marker = "  ←" if focused and focused.id == f.id else ""

            yield write_text(f"[{i}] {label} - {state}{marker}\n")

    async def _stop_job(self, request: Request):

        flow, index = self._get_flow_by_index(request)

        if not flow:
            yield write_text(f"Job {index} nicht gefunden")

        self.ctx.session.del_flow(flow)
        yield write_text(f"Job {index} gestoppt")

    async def _use_job(self, request: Request):

        flow, index = self._get_flow_by_index(request)

        if not flow:
            yield write_text(f"Job {index} nicht gefunden")
            return

        self.ctx.session.set_interaction(flow.id)
        yield write_text(f"Fokus auf Job {index} gesetzt")
