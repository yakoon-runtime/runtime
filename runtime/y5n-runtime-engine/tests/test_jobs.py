from __future__ import annotations

import pytest
from y5n.runtime.api.flow.primitives import Pulse, Stop, Suspend, YieldToScheduler


@pytest.mark.asyncio
async def test_suspend_blocks_then_resume(harness):
    """A suspended flow is not runnable until resumed."""

    async def my_handler(ctx):
        yield Pulse(control=Suspend())
        yield Pulse()

    flow = await harness.start(my_handler)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Suspend)
    assert not flow.control.is_runnable(flow, harness.session)

    await flow.control.resume(flow, harness.session)
    assert isinstance(flow.control, YieldToScheduler)
    assert flow.control.is_runnable(flow, harness.session)

    pulse = await harness.run_until_blocked(flow)
    assert isinstance(pulse.control, Stop)
    assert harness.session.get_flow(flow.id) is None
