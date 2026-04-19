from typing import Protocol

from yakoon.base.runtime import InputContext


class Session(Protocol):
    pass


class Projection(Protocol):
    pass


class Output(Protocol):

    async def send_projection(
        self,
        session: Session,
        projection: Projection,
        *,
        ctx: InputContext | None,
        job_id: str = "system",
    ): ...
