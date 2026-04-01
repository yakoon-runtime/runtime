from yakoon.base.projection import ProjectionEvent, ProjectionHeader
from yakoon.base.projection.transport import Patch, PatchOp, PatchReset


class ViewEmitter:

    def begin(
        self, header: ProjectionHeader, *, vid: str, job_id: str
    ) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            header=header,
            patch=Patch(ops=[PatchReset()], final=False),
            job_id=job_id,
        )

    def emit(self, vid: str, ops: list[PatchOp], *, job_id: str) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            patch=Patch(ops=ops, final=False),
            job_id=job_id,
        )

    def finish(self, vid: str, *, job_id: str) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            patch=Patch(ops=[], final=True),
            job_id=job_id,
        )
