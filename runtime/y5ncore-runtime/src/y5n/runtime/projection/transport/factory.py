from y5n.base.projection import ProjectionEvent, ProjectionHeader
from y5n.base.projection.transfer import Patch, PatchOp, PatchReset
from y5n.base.runtime import InputContext


class EventFactory:

    def begin_event(
        self,
        header: ProjectionHeader,
        *,
        vid: str,
        ctx: InputContext | None,
        job_id: str,
    ) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            header=header,
            ctx=ctx,
            patch=Patch(ops=[PatchReset()], final=False),
            job_id=job_id,
        )

    def patch_event(
        self,
        vid: str,
        ops: list[PatchOp],
        *,
        job_id: str,
        ctx: InputContext | None,
    ) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            ctx=ctx,
            patch=Patch(ops=ops, final=False),
            job_id=job_id,
        )

    def finish_event(
        self,
        vid: str,
        *,
        job_id: str,
        ctx: InputContext | None,
    ) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            ctx=ctx,
            patch=Patch(ops=[], final=True),
            job_id=job_id,
        )
