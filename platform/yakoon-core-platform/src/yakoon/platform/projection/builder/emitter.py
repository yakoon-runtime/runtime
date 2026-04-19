from yakoon.base.projection import ProjectionEvent, ProjectionHeader
from yakoon.base.projection.transfer import Patch, PatchOp, PatchReset
from yakoon.base.runtime import InputContext


class ViewEmitter:

    def begin(
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

    def emit(
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

    def finish(
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
