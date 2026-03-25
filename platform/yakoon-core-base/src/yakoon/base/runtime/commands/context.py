from dataclasses import dataclass
from typing import cast

from yakoon.base.runtime.controllers.controller import Controller
from yakoon.base.runtime.sessions import CommandSession, Session


@dataclass(frozen=True, slots=True)
class CommandContext:

    session: CommandSession
    controller: Controller

    @property
    def system(self) -> Session:
        return cast(Session, self.session)
