from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.flow import out
from yakoon.base.projection import to_text
from yakoon.base.sources import DataRequest, OnDataSource


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL
    anonymous = True

    def __init__(
        self,
        on_source: OnDataSource,
        on_has_interaction: OnHasInteraction,
        on_set_interaction: OnSetInteraction,
        on_get_active_app: OnGetActiveApp,
        on_set_active_app: OnSetActiveApp,
        on_save_session: OnSaveSession,
    ):
        self.on_source = on_source
        self.on_has_interaction = on_has_interaction
        self.on_set_interaction = on_set_interaction
        self.on_get_active_app = on_get_active_app
        self.on_set_active_app = on_set_active_app
        self.on_save_session = on_save_session

    async def run(self, request: Request):

        # --------------------------------------------------
        # 1. Fokus verlassen (höchste Priorität)
        # --------------------------------------------------
        if self.on_has_interaction():
            self.on_set_interaction(None)
            yield out(to_text("↩ Fokus verlassen"))
            return

        # --------------------------------------------------
        # 2. Controller verlassen
        # --------------------------------------------------
        result = await self.on_source(DataRequest("system:apps --shell"))
        shell = result.one()

        current = self.on_get_active_app()
        if shell["id"] != current:
            self.on_set_active_app(shell["id"])
            await self.on_save_session()
            current = shell["id"]

        yield out(to_text(f"Aktuell: {current}"))


# ----------------------------------
# PORTS
# ----------------------------------


class OnHasInteraction(Protocol):
    def __call__(self) -> bool: ...


class OnSetInteraction(Protocol):
    def __call__(self, flow_id: str | None) -> None: ...


class OnGetActiveApp(Protocol):
    def __call__(self) -> str | None: ...


class OnSetActiveApp(Protocol):
    def __call__(self, app_id: str) -> None: ...


class OnSaveSession(Protocol):
    async def __call__(self) -> None: ...
