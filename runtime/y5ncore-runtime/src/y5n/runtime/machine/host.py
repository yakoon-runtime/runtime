from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from y5n.base.clients.connection import ClientConnection
from y5n.base.naming.key import Key
from y5n.base.runtime import RuntimeInfo
from y5n.runtime.runtime import Session

from .runner import Runner


class RuntimeHost:
    """Top-level runtime host.

    Manages sessions, client connections, and the session lifecycle
    (connect, disconnect, receive_input).  Wires sessions to the
    Runner and Scheduler.
    """

    def __init__(
        self,
        *,
        on_schedule: OnSchedule,
        on_join_bus: OnJoinBus,
        on_get_session: OnGetSession,
        on_create_runner: OnCreateRunner,
        on_setup: OnSetup,
        known_runtimes: dict[str, str] | None = None,
        info: RuntimeInfo,
    ):
        self.on_flow_schedule = on_schedule
        self.on_join_bus = on_join_bus
        self.on_get_session = on_get_session
        self.on_create_runner = on_create_runner
        self.on_setup = on_setup
        self.known_runtimes = known_runtimes or {}
        self.info = info

        self._sessions: dict[Key, Runner] = {}
        self._connections: dict[ClientConnection, Runner] = {}
        self._session_counter = 0
        self._session_done: dict[str, Callable] = {}

        asyncio.create_task(self.on_flow_schedule())

    async def setup(self):
        session = await self.on_get_session()
        await self.on_setup(session)

    def register_session_done(
        self, session_key: str, callback: Callable[[], Awaitable[None]]
    ) -> None:
        self._session_done[session_key] = callback

    def resolve_runtime(self, name: str) -> str:
        if "://" in name:
            return name
        return self.known_runtimes[name]

    async def flow_complete(self, flow, session) -> None:
        done = self._session_done.get(str(session.key))
        if done:
            await done()

    async def connect(
        self,
        connection: ClientConnection,
        session_key: Key | None = None,
    ):
        connection.runtime_info = self.info
        self.on_join_bus(client=connection)

        # attach existing session
        if session_key and session_key in self._sessions:
            runner = self._sessions[session_key]

        # create new session
        else:
            session = await self.on_get_session()

            runner = self.on_create_runner(session=session)
            self._sessions[session.key] = runner

            # await self.engine.dispatch(session, initial_command)

        self._connections[connection] = runner
        return runner.session

    async def disconnect(self, connection: ClientConnection):
        runner = self._connections.pop(connection, None)
        if not runner:
            return

        # has session other clients
        if self._has_connections(runner):
            return

        # real session is death
        session = runner.session

        # self.engine.cleanup_session(session)
        self._sessions.pop(session.key, None)

    async def receive_input(self, connection, event):
        runner = self._connections.get(connection)
        if runner is None:
            raise RuntimeError("receive_input() has no runner for connection")

        await runner.on_input(event)

    def _has_connections(self, runner: Runner) -> bool:
        return any(r is runner for r in self._connections.values())


# ----------------------------------
# PORTS
# ----------------------------------


class OnSchedule(Protocol):
    async def __call__(self): ...


class OnJoinBus(Protocol):
    def __call__(self, *, client: ClientConnection): ...


class OnGetSession(Protocol):
    async def __call__(self) -> Session: ...


class OnCreateRunner(Protocol):
    def __call__(self, *, session) -> Runner: ...


class OnSetup(Protocol):
    async def __call__(self, session) -> None: ...
