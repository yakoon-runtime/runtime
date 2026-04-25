from typing import Protocol, cast

from yakoon.base.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.flow.patterns import write_text
from yakoon.base.runtime.sessions.port import SessionStore


class _ControllerAccess(Protocol):
    def get_active_app(self) -> str: ...
    def set_active_app(self, controller_id: str) -> None: ...
    def set_interaction(self, flow_id: str | None): ...
    def has_interaction(self) -> bool: ...


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL

    async def run(self, request: Request):

        sys_session = self.ctx.session
        # privileged access: controller management
        access = cast(_ControllerAccess, sys_session)

        # 1. Fokus verlassen (höchste Priorität)
        # --------------------------------------------------
        if access.has_interaction():
            access.set_interaction(None)
            yield write_text("↩ Fokus verlassen")
            return

        # --------------------------------------------------
        # 2. Controller verlassen
        # --------------------------------------------------
        app_query = self.container.get(ApplicationQuery)
        shell = app_query.shell()

        current = access.get_active_app()

        if shell.id != current:
            access.set_active_app(shell.id)
            await self.container.get(SessionStore).save(sys_session)
            current = shell.id

        yield write_text(f"Kontroller: {current}")
