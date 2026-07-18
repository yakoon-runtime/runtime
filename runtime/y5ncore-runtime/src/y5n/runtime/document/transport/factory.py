from y5n.base.document import DocumentEvent, DocumentHeader
from y5n.base.document.transfer import Patch, PatchOp, PatchReset
from y5n.base.runtime import InputContext


class EventFactory:

    def begin_event(
        self,
        header: DocumentHeader,
        *,
        vid: str,
        ctx: InputContext | None,
        job_id: str,
        view_params: dict | None = None,
    ) -> DocumentEvent:
        return DocumentEvent(
            id=vid,
            header=header,
            ctx=ctx,
            patch=Patch(ops=[PatchReset()], final=False),
            job_id=job_id,
            view_params=view_params,
        )

    def patch_event(
        self,
        vid: str,
        ops: list[PatchOp],
        *,
        job_id: str,
        ctx: InputContext | None,
    ) -> DocumentEvent:
        return DocumentEvent(
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
    ) -> DocumentEvent:
        return DocumentEvent(
            id=vid,
            ctx=ctx,
            patch=Patch(ops=[], final=True),
            job_id=job_id,
        )
