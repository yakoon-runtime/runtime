from yakoon.base.runtime.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
)
from yakoon.base.ui import v_text


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
            yield show(v_text(f"Unbekannte Aktion: {action}"))

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _enumerate_flows(self):
        session = self.context.system
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
            yield show(v_text("Keine Jobs aktiv."))
            return

        yield show(v_text("Aktive Jobs:\n"))

        focused = self.context.system.focused_flow
        for i, f in indexed:
            label = getattr(f, "label", f.command_key)
            state = f.state.name
            marker = " *" if focused and focused.id == f.id else ""

            yield show(v_text(f"[{i}] {label} - {state}{marker}\n"))

    async def _stop_job(self, request: Request):

        flow, index = self._get_flow_by_index(request)

        if not flow:
            yield show(v_text(f"Job {index} nicht gefunden"))

        self.context.system.del_flow(flow)
        yield show(v_text(f"Job {index} gestoppt"))

    async def _use_job(self, request: Request):

        flow, index = self._get_flow_by_index(request)

        if not flow:
            yield show(v_text(f"Job {index} nicht gefunden"))
            return

        self.context.system.set_focus(flow.id)
        yield show(v_text(f"Fokus auf Job {index} gesetzt"))
