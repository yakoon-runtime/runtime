from yakoon.base.ui.event import ViewEvent
from yakoon.base.ui.patch import Patch, PatchOp, PatchReset


class ViewEmitter:

    def begin(self, vid: str) -> ViewEvent:
        return ViewEvent(
            id=vid,
            patch=Patch(ops=[PatchReset()], final=False),
        )

    def emit(self, vid: str, ops: list[PatchOp]) -> ViewEvent:
        return ViewEvent(
            id=vid,
            patch=Patch(ops=ops, final=False),
        )

    def finish(self, vid: str) -> ViewEvent:
        return ViewEvent(
            id=vid,
            patch=Patch(ops=[], final=True),
        )
