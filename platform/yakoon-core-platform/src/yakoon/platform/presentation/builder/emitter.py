from yakoon.base.presentation import Patch, PatchOp, PatchReset, ViewEvent, ViewHeader


class ViewEmitter:

    def begin(self, header: ViewHeader, vid: str) -> ViewEvent:
        return ViewEvent(
            id=vid,
            header=header,
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
