from typing import Protocol


class Session(Protocol):
    pass


class View(Protocol):
    pass


class OutputStream(Protocol):

    async def send_view(self, session: Session, view: View): ...
