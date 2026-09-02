"""Session Startup Sequence (ADR-25, Slice 2B): serial execution on CREATE.

A keyless connect creates a NEW session and runs the declared startup
commands one at a time as ordinary Runtime invocations. Startup
serializes Flow completion (Scheduler.when_complete), not command
success. Startup Flows carry no out_channel — their output takes the
normal projection path. Resume paths never trigger startup.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import out, receive
from y5n.runtime.api.flow.primitives import AwaitEvent
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import Event
from y5n.runtime.engine.machine.manager import RuntimeManager
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.runtime import Session
from y5n.runtime.engine.runtime.sessions.session import SessionData
from y5n.runtime.engine.services.permissions import PermissionChecker
from y5n.runtime.engine.settings import Settings
from y5n.runtime.engine.wire.machine import build_machine


class _Client:
    """Minimal client connection for RuntimeManager.connect."""

    def __init__(self):
        self.runtime_info = None
        self.session_key = None

    async def emit(self, event):
        pass


def _build_platform(executed: list[str]) -> Node:
    """In-memory command tree with an anonymous /usr/bin/err node."""

    def plain(key: str):
        async def run():
            executed.append(key)
            yield out({"cmd": key})

        return run

    async def gate_run():
        executed.append("gate")
        yield out({"cmd": "gate"})
        yield receive()
        executed.append("gate-resumed")
        yield out({"cmd": "gate-resumed"})

    async def boom_run():
        executed.append("boom")
        raise RuntimeError("boom")
        yield out({"cmd": "unreachable"})

    async def err_run():
        executed.append("err")
        yield out({"cmd": "err"})

    root = Node(key="root")
    for key in ("first", "second", "third", "after"):
        root.add(Node(key=key, anonymous=True, run=plain(key)))
    root.add(Node(key="gate", anonymous=True, run=gate_run))
    root.add(Node(key="boom", anonymous=True, run=boom_run))
    # "protected" stays non-anonymous: it requires ordinary authorization.
    root.add(Node(key="protected", run=plain("protected")))
    bin_node = Node(key="bin")
    bin_node.add(Node(key="err", anonymous=True, run=err_run))
    usr_node = Node(key="usr")
    usr_node.mount(bin_node)
    root.mount(usr_node)
    return root


def _build_machine(
    startup: tuple[str, ...],
    executed: list[str],
    documents: list[dict],
    resumed: list[Key],
) -> RuntimeManager:
    """The real wire machine over the in-memory command tree."""

    async def on_projection_send(
        *, session, document, ctx, job_id="system", mode="replace", view_params=None
    ):
        documents.append(document)

    async def on_session(*, key: Key, **kwargs):
        session = Session(key=key, data=SessionData())
        return session, True

    async def on_resume_session(key: Key) -> Session:
        resumed.append(key)
        return Session(key=key, data=SessionData())

    return build_machine(
        platform=_build_platform(executed),
        on_suggest=lambda **kwargs: [],
        on_projection_send=on_projection_send,
        on_session=on_session,
        on_resume_session=on_resume_session,
        on_has_permission=PermissionChecker().check,
        on_audit_warning=lambda **kwargs: None,
        on_activity=AsyncMock(),
        on_initialize=AsyncMock(),
        known_runtimes={},
        settings=Settings(),
        on_get_node=lambda parent, key: parent.get(key),
        startup=startup,
    )


async def _settle(rounds: int = 50):
    for _ in range(rounds):
        await asyncio.sleep(0)


async def _shutdown(manager: RuntimeManager):
    scheduler = manager.on_flow_schedule.__self__
    scheduler._running = False
    scheduler._event.set()
    await _settle(5)


# ----------------------------------------
# 1. EMPTY STARTUP
# ----------------------------------------


async def test_empty_startup_dispatches_nothing():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine((), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()
    await _shutdown(manager)

    assert client.session_key is not None
    assert executed == []
    assert documents == []
    assert list(session.flows()) == []


# ----------------------------------------
# 2. SINGLE COMMAND
# ----------------------------------------


async def test_single_startup_command_executes_exactly_once():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("first",), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)

    # The creating client is joined before the first dispatch happens.
    assert client in session._bus._clients
    assert executed == []

    await _settle()
    await _shutdown(manager)

    assert executed == ["first"]
    assert [d["cmd"] for d in documents] == ["first"]
    assert list(session.flows()) == []


# ----------------------------------------
# 3. ORDER
# ----------------------------------------


async def test_startup_commands_execute_in_declaration_order():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("first", "second", "third"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()
    await _shutdown(manager)

    assert executed == ["first", "second", "third"]
    assert [d["cmd"] for d in documents] == ["first", "second", "third"]
    assert list(session.flows()) == []


# ----------------------------------------
# 4. REAL COMPLETION BARRIER
# ----------------------------------------


async def test_parked_startup_flow_blocks_the_next_startup_item():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("gate", "second"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()

    # first starts, parks on AwaitEvent, second has NOT started
    assert executed == ["gate"]
    flows = list(session.flows())
    assert len(flows) == 1
    gate_flow = flows[0]
    assert isinstance(gate_flow.control, AwaitEvent)
    # parked on user input — not on a completion channel
    assert gate_flow.out_channel is None

    # deliver the continuation the same way Runner.on_input does
    session.push_event(
        Scope.USER_INPUT,
        "__user__",
        Event(payload="go"),
        flow=gate_flow,
    )
    scheduler = manager.on_flow_schedule.__self__
    scheduler.schedule_flow(gate_flow, session)
    await _settle()
    await _shutdown(manager)

    assert executed == ["gate", "gate-resumed", "second"]
    assert list(session.flows()) == []


# ----------------------------------------
# 5. COMPLETION, NOT SUCCESS
# ----------------------------------------


async def test_failed_but_completed_command_advances_the_sequence():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("boom", "after"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()
    await _shutdown(manager)

    # The handler raised; the flow completed through the ordinary error
    # path (/usr/bin/err) and the sequence advanced.
    assert executed == ["boom", "err", "after"]
    assert [d["cmd"] for d in documents] == ["err", "after"]
    assert list(session.flows()) == []


# ----------------------------------------
# 6. AUTHORIZATION
# ----------------------------------------


async def test_startup_does_not_bypass_authorization():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("protected", "after"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()
    await _shutdown(manager)

    # The protected command never ran; the anonymous session got the
    # ordinary PermissionDenied → /usr/bin/err path — and because that
    # Flow completed, the sequence advanced.
    assert "protected" not in executed
    assert executed == ["err", "after"]
    assert [d["cmd"] for d in documents] == ["err", "after"]
    assert list(session.flows()) == []


# ----------------------------------------
# 6b. ESCAPING DISPATCH EXCEPTION ABORTS THE SEQUENCE
# ----------------------------------------


async def test_escaping_dispatch_exception_aborts_and_is_reported(caplog):
    """An exception that escapes engine.dispatch is an unexpected
    infrastructure failure — never reinterpreted as 'no Flow'.

    An unterminated shell quote makes the parser raise before any Flow
    exists. The startup task must abort the remaining sequence and the
    detached task's done-callback must retrieve and report the failure.
    """

    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("echo 'unterminated", "after"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    with caplog.at_level(logging.ERROR, logger="y5n.runtime.engine.wire.machine"):
        await _settle()
    await _shutdown(manager)

    # the sequence aborted: no error Flow, no later startup item
    assert executed == []
    assert list(session.flows()) == []

    # the detached task's exception was retrieved and reported
    records = [r for r in caplog.records if "startup task failed" in r.message]
    assert len(records) == 1
    assert isinstance(records[0].exc_info[1], ValueError)


# ----------------------------------------
# 7. CREATE ONLY
# ----------------------------------------


async def test_same_process_resume_does_not_run_startup_again():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("first",), executed, documents, [])

    first = _Client()
    await manager.connect(first)
    await _settle()
    assert executed == ["first"]

    # additional client joins the live session — no startup
    second = _Client()
    await manager.connect(second, session_key=Key.from_str(first.session_key))
    await _settle()
    await _shutdown(manager)

    assert executed == ["first"]
    assert second.session_key == first.session_key


async def test_process_boundary_resume_does_not_run_startup():
    executed: list[str] = []
    documents: list[dict] = []
    resumed: list[Key] = []
    manager = _build_machine(("first",), executed, documents, resumed)

    client = _Client()
    key = Key.from_parts("system", "session", "runtime", "earlier-boot-0")
    session = await manager.connect(client, session_key=key)
    await _settle()
    await _shutdown(manager)

    assert resumed == [key]
    assert executed == []
    assert session.key == key


# ----------------------------------------
# 8. OUTPUT PATH
# ----------------------------------------


async def test_startup_output_uses_the_normal_projection_path():
    executed: list[str] = []
    documents: list[dict] = []
    manager = _build_machine(("first", "second"), executed, documents, [])

    client = _Client()
    session = await manager.connect(client)
    await _settle()
    await _shutdown(manager)

    # Documents arrived through the ordinary projection callback …
    assert [d["cmd"] for d in documents] == ["first", "second"]
    # … and no completion channel was ever created: startup Flows carry
    # no out_channel, so nothing was pushed into session mailboxes.
    assert session._channels == {}
