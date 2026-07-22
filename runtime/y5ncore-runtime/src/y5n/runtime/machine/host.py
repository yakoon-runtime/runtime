from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from y5n.runtime.api.clients.connection import ClientConnection
from y5n.runtime.api.naming.key import Key
from y5n.runtime.api.runtime import RuntimeInfo
from y5n.runtime.runtime import Session

from .runner import Runner


class RuntimeHost:
    """Top-level runtime host.

    Manages sessions, client connections, and the session lifecycle.
    A connection can subscribe to multiple sessions (observing their
    projections) but has exactly one active session that receives input.
    """

    def __init__(
        self,
        *,
        on_schedule: OnSchedule,
        on_get_session: OnGetSession,
        on_create_runner: OnCreateRunner,
        on_setup: OnSetup,
        known_runtimes: dict[str, str] | None = None,
        info: RuntimeInfo,
    ):
        self.on_flow_schedule = on_schedule
        self.on_get_session = on_get_session
        self.on_create_runner = on_create_runner
        self.on_setup = on_setup
        self.known_runtimes = known_runtimes or {}
        self.info = info

        self._sessions: dict[Key, Runner] = {}
        self._subscriptions: dict[ClientConnection, set[Runner]] = {}
        self._connection_home: dict[ClientConnection, Runner] = {}
        self._active: dict[ClientConnection, Runner] = {}
        self._session_done: dict[str, list[Callable]] = {}

        asyncio.create_task(self.on_flow_schedule())

    async def setup(self):
        session = await self.on_get_session()
        await self.on_setup(session)

    def register_session_done(
        self, session_key: str, callback: Callable[[], Awaitable[None]]
    ) -> None:
        self._session_done.setdefault(session_key, []).append(callback)

    def resolve_runtime(self, name: str) -> str:
        if "://" in name:
            return name
        return self.known_runtimes[name]

    async def flow_complete(self, flow, session) -> None:
        for cb in self._session_done.get(str(session.key), []):
            await cb()
        runner = self._sessions.get(session.key)
        if runner:
            self._maybe_cleanup(runner)

    async def connect(
        self,
        connection: ClientConnection,
        session_key: Key | None = None,
    ):
        connection.runtime_info = self.info

        if session_key and session_key in self._sessions:
            runner = self._sessions[session_key]
        else:
            session = await self.on_get_session()
            runner = self.on_create_runner(session=session)
            self._sessions[session.key] = runner

        runner.session.join(connection)
        self._subscriptions.setdefault(connection, set()).add(runner)
        self._connection_home[connection] = runner
        self._active[connection] = runner
        return runner.session

    async def disconnect(self, connection: ClientConnection):
        subs = self._subscriptions.pop(connection, None)
        self._active.pop(connection, None)
        self._connection_home.pop(connection, None)
        if not subs:
            return

        for runner in subs:
            runner.session.leave(connection)
            self._maybe_cleanup(runner)

    async def receive_input(self, connection, event):
        runner = self._active[connection]
        await runner.on_input(event)

    def _has_subscribers(self, runner: Runner) -> bool:
        return any(runner in subs for subs in self._subscriptions.values())

    def _maybe_cleanup(self, runner: Runner) -> None:
        if self._has_subscribers(runner):
            return
        if len(list(runner.session.flows())) > 0:
            return
        self._sessions.pop(runner.session.key, None)

    def list_sessions(self) -> list[dict]:
        rows = []
        for key, runner in self._sessions.items():
            clients = sum(1 for subs in self._subscriptions.values() if runner in subs)
            homes = sum(1 for home in self._connection_home.values() if home is runner)
            flows = len(list(runner.session.flows()))
            rows.append(
                {
                    "key": str(key),
                    "clients": clients,
                    "homes": homes,
                    "flows": flows,
                }
            )
        return rows

    async def attach_session(self, session: Session, target_key: str):
        runner = self._sessions.get(session.key)
        if not runner:
            raise RuntimeError(f"Session {session.key} not found")

        target = Key.from_str(target_key)
        target_runner = self._sessions.get(target)
        if not target_runner:
            raise RuntimeError(f"Target session {target_key} not found")

        if target == runner.session.key:
            return

        connections = [c for c, r in self._active.items() if r is runner]

        for conn in connections:
            target_runner.session.join(conn)
            self._subscriptions.setdefault(conn, set()).add(target_runner)
            self._active[conn] = target_runner

    async def detach_session(self, session: Session):
        runner = self._sessions.get(session.key)
        if not runner:
            raise RuntimeError(f"Session {session.key} not found")

        for conn, active in list(self._active.items()):
            if active is not runner:
                continue
            home = self._connection_home.get(conn)
            if home is runner:
                continue
            runner.session.leave(conn)
            self._subscriptions.get(conn, set()).discard(runner)
            if home is None:
                self._active.pop(conn, None)
            else:
                self._active[conn] = home

        self._maybe_cleanup(runner)


# ----------------------------------
# PORTS
# ----------------------------------


class OnSchedule(Protocol):
    async def __call__(self): ...


class OnGetSession(Protocol):
    async def __call__(self) -> Session: ...


class OnCreateRunner(Protocol):
    def __call__(self, *, session) -> Runner: ...


class OnSetup(Protocol):
    async def __call__(self, session) -> None: ...
