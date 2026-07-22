from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from support.runtime import RuntimeHarness
from y5n.runtime.engine.naming import Key
from y5n.runtime.engine.nodes import Node
from y5n.runtime.machine.effects import EffectExecutor
from y5n.runtime.machine.engine import CommandEngine
from y5n.runtime.machine.scheduler import Scheduler
from y5n.runtime.runtime.sessions.session import Session, SessionData


async def _passthrough_intercept(*, node, tokens, session, context):
    return node, tokens


@pytest.fixture
def session():
    return Session(
        key=Key.from_parts("test", "session", "runtime", "test-1"),
        data=SessionData(),
    )


@pytest.fixture
def effect_executor():
    return EffectExecutor(
        on_projection=AsyncMock(),
        on_start_task=AsyncMock(),
        on_start_command=AsyncMock(),
    )


@pytest.fixture
def engine(effect_executor):
    return CommandEngine(
        on_resolve_node=AsyncMock(return_value=(None, [])),
        on_parse_input=AsyncMock(return_value=("", [], [])),
        on_intercept=_passthrough_intercept,
        on_apply_effects=effect_executor.execute,
    )


@pytest.fixture
def scheduler(engine):
    return Scheduler(
        platform=Node(key="root"),
        on_setup=AsyncMock(return_value=None),
        on_dispatch=AsyncMock(return_value=None),
        on_step_flow=engine.step_flow,
        on_show_projection=AsyncMock(),
        on_audit_warning=lambda **kw: None,
        on_error_resolve=AsyncMock(return_value=None),
        on_flow_complete=AsyncMock(),
    )


@pytest.fixture
def harness(session, scheduler, engine):
    return RuntimeHarness(session=session, scheduler=scheduler, engine=engine)
