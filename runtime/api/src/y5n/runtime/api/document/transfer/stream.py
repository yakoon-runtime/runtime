from typing import Protocol

from y5n.runtime.api.runtime import InputContext


class Session(Protocol):
    pass


class Document(Protocol):
    pass


class Output(Protocol):

    async def send_document(
        self,
        session: Session,
        document: Document,
        *,
        ctx: InputContext | None,
        job_id: str = "system",
    ): ...
