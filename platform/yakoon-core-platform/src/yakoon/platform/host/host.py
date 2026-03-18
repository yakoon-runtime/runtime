from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from yakoon.base.capabilities.identity.port import PermissionService
from yakoon.base.clients.connection import ClientConnection
from yakoon.base.host import FormInput, TextInput
from yakoon.base.runtime import SessionService
from yakoon.base.values.key import Key
from yakoon.platform.runtime.bus import BusOutput, SessionBus

if TYPE_CHECKING:
    from yakoon.platform.engine.engine import CommandEngine

from .runner import Runner


class RuntimeHost:

    def __init__(self, engine: CommandEngine, bus: SessionBus):
        self.engine = engine
        self.bus = bus

        self._sessions: dict[Key, Runner] = {}
        self._connections: dict[ClientConnection, Runner] = {}
        self._runner_tasks: dict[int, asyncio.Task] = {}
        self._session_counter = 0

    async def connect(
        self,
        connection: ClientConnection,
        interaction,
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
                interaction=interaction,
            )
            self._sessions[session.key] = runner

            task = asyncio.create_task(runner.start([]))
            self._runner_tasks[self._runner_key(runner)] = task

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

        # cancel task
        task = self._runner_tasks.pop(self._runner_key(runner), None)
        if task:
            task.cancel()

        self.engine.cleanup_session(session)
        self._sessions.pop(session.key, None)

    async def receive_input(self, connection: ClientConnection, event):
        runner = self._connections.get(connection)
        if runner is None:
            raise RuntimeError("No runner for connection.")

        if isinstance(event, FormInput):
            await runner.on_input_submit(event.data)
        elif isinstance(event, TextInput):
            await runner.on_user_input(event.value)

    async def create_session(self):

        key = self.next_session_key()

        sessions = self.engine.services.get(SessionService)
        session, _ = await sessions.get_or_create(key)

        permissions = self.engine.services.get(PermissionService)
        permissions.set_bootstrap_permissions(session)

        return session

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
