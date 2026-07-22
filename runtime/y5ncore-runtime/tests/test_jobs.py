from __future__ import annotations

import pytest
from y5n.runtime.engine.flow.primitives import Outcome, Stop, Suspend, YieldToScheduler


@pytest.mark.asyncio
async def test_suspend_blocks_then_resume(harness):
    """A suspended flow is not runnable until resumed."""

    async def my_handler(ctx):
        yield Outcome(control=Suspend())
        yield Outcome()

    flow = await harness.start(my_handler)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Suspend)
    assert not flow.control.is_runnable(flow, harness.session)

    await flow.control.resume(flow, harness.session)
    assert isinstance(flow.control, YieldToScheduler)
    assert flow.control.is_runnable(flow, harness.session)

    outcome = await harness.run_until_blocked(flow)
    assert isinstance(outcome.control, Stop)
    assert harness.session.get_flow(flow.id) is None
