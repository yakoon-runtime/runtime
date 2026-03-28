from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

from yakoon.base.capabilities.identity.port import PermissionService
from yakoon.base.clients.connection import ClientConnection
from yakoon.base.naming.key import Key
from yakoon.base.runtime.sessions import SessionService
from yakoon.platform.host.scheduler import Scheduler
from yakoon.platform.runtime.bus import BusOutput, SessionBus
from yakoon.platform.runtime.sessions import Session as PlatformSession

if TYPE_CHECKING:
    from yakoon.platform.engine import CommandEngine

from .runner import Runner


class RuntimeHost:

    def __init__(self, engine: CommandEngine, bus: SessionBus):
        self.engine = engine
        self.bus = bus

        self._sessions: dict[Key, Runner] = {}
        self._connections: dict[ClientConnection, Runner] = {}
        self._session_counter = 0
        self.scheduler = Scheduler(engine)

        asyncio.create_task(self.scheduler.run())

    async def connect(
        self,
        connection: ClientConnection,
        session_key: Key | None = None,
    ):
        self.bus.join(connection)

        # attach existing session
        if session_key and session_key in self._sessions:
            runner = self._sessions[session_key]

        # create new session
        else:
            session = await self.create_session()
            session.bind_io(BusOutput(self.bus))
            runner = Runner(
                engine=self.engine,
                session=session,
                scheduler=self.scheduler,
            )
            self._sessions[session.key] = runner

            # initial_command = DispatchInput("")
            # await self.engine.dispatch(session, initial_command)

        self._connections[connection] = runner
        return connection

    async def disconnect(self, connection: ClientConnection):
        runner = self._connections.pop(connection, None)
        if not runner:
            return

        # has session other clients
        if self._has_connections(runner):
            return

        # real session ist deth
        session = runner.session

        # self.engine.cleanup_session(session)
        self._sessions.pop(session.key, None)

    async def receive_input(self, connection, event):
        runner = self._connections.get(connection)
        if runner is None:
            raise RuntimeError("No runner for connection.")

        await runner.on_input(event)

    async def create_session(self) -> PlatformSession:

        key = self.next_session_key()

        sessions = self.engine.services.get(SessionService)
        session, _ = await sessions.get_or_create(key)

        permissions = self.engine.services.get(PermissionService)
        permissions.set_bootstrap_permissions(session)

        return cast(PlatformSession, session)

    def next_session_key(self) -> Key:

        self._session_counter += 1

        return Key.from_parts(
            "system",
            "session",
            "runtime",
            str(self._session_counter),
        )

    def _has_connections(self, runner: Runner) -> bool:
        return any(r is runner for r in self._connections.values())

    def _runner_key(self, runner: Runner) -> int:
        return id(runner)
