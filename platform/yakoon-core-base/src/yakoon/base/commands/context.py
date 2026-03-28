from dataclasses import dataclass

from yakoon.base.controllers.controller import Controller
from yakoon.base.runtime.sessions import Session


@dataclass(frozen=True, slots=True)
class CommandContext:

    session: Session
    controller: Controller
