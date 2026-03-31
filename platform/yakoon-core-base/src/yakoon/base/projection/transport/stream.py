from typing import Protocol


class Session(Protocol):
    pass


class Projection(Protocol):
    pass


class Output(Protocol):

    async def send_projection(self, session: Session, projection: Projection): ...
