from y5n.base.flow.channel import Scope
from y5n.base.flow.primitives import Effect, EmitView
from y5n.base.runtime import Event
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class EmitViewHandler:
    """Handles EmitView: sends a document to the output layer.

    If the flow has an out_channel the document is routed as a
    session event.  Otherwise it is sent directly to the registered
    projection callback with the appropriate context and job id.
    Supports persisting the view on the flow and explicit context/job
    id overrides via the effect fields.
    """

    def __init__(self, on_projection):
        self._on_projection = on_projection

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        if not isinstance(effect, EmitView):
            return
        e = effect

        if flow.out_channel:
            session.push_event(
                Scope.SESSION,
                flow.out_channel,
                Event(payload=e.view),
            )
            return

        ctx = e.ctx or flow.event.context
        view = e.view

        if e.persist:
            flow.view = view

        job_id = e.job_id or (f"{flow.id}:{e.space}" if e.space else flow.id)

        await self._on_projection(
            session=session,
            document=view,
            ctx=ctx,
            job_id=job_id,
            mode=e.mode,
            view_params=e.view_params,
        )
