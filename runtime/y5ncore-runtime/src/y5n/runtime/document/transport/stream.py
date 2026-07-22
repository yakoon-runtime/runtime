from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typing_extensions import Protocol
from y5n.runtime.api.document.normalize import normalize as _normalize
from y5n.runtime.api.runtime import InputContext

_log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from y5n.runtime.runtime import Session


class EventStreamOutput:
    """
    High-level document streaming.

    Responsibilities:
    - lifecycle (begin / abort / finish)
    - block-aware dispatching
    - error safety
    """

    def __init__(
        self,
        on_begin: OnBeginDocument,
        on_emit: OnEmitDocument,
        on_abort: OnAbortDocument,
        on_finish: OnFinishDocument,
    ):
        self.on_begin = on_begin
        self.on_emit = on_emit
        self.on_abort = on_abort
        self.on_finish = on_finish

    async def send_document(
        self,
        session: Session,
        document: dict,
        *,
        ctx: InputContext | None,
        job_id: str = "system",
        mode: str = "replace",
        view_params: dict | None = None,
    ):
        document = _normalize(document)

        await self.on_begin(
            session=session,
            document=document,
            ctx=ctx,
            job_id=job_id,
            reset=(mode == "replace"),
            view_params=view_params,
        )

        try:
            await self.on_emit(
                session=session,
                document=document,
            )

        except Exception as exc:
            _log.exception("emit failed: %s", exc)
            try:
                await self.on_abort(
                    session=session,
                    projection_id=document["id"],
                )
            except Exception as abort_exc:
                _log.exception("abort also failed: %s", abort_exc)

        else:
            await self.on_finish(
                session=session,
                document=document,
            )


# -------------
# --- PORTS ---
# -------------


class OnBeginDocument(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        document: dict,
        ctx: InputContext | None,
        job_id: str,
        reset: bool = True,
        view_params: dict | None = None,
    ) -> None: ...


class OnEmitDocument(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        document: dict,
    ) -> None: ...


class OnAbortDocument(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection_id: str,
    ) -> None: ...


class OnFinishDocument(Protocol):

    async def __call__(
        self,
        *,
        session: Session,
        document: dict,
    ) -> None: ...
