from yakoon.base.projection import ProjectionEvent, ProjectionHeader
from yakoon.base.projection.transport import Patch, PatchOp, PatchReset


class ViewEmitter:

    def begin(self, header: ProjectionHeader, vid: str) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            header=header,
            patch=Patch(ops=[PatchReset()], final=False),
        )

    def emit(self, vid: str, ops: list[PatchOp]) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            patch=Patch(ops=ops, final=False),
        )

    def finish(self, vid: str) -> ProjectionEvent:
        return ProjectionEvent(
            id=vid,
            patch=Patch(ops=[], final=True),
        )
