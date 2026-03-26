from dataclasses import dataclass

from yakoon.base.runtime.controllers.controller import Controller
from yakoon.base.runtime.sessions import Session


@dataclass(frozen=True, slots=True)
class CommandContext:

    session: Session
    controller: Controller
