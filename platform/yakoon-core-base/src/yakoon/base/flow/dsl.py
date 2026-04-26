"""
DSL - Runtime Interaction Language

This module defines the *core language* of the runtime.

These functions are the ONLY allowed way for a flow to:
- emit UI
- wait for input or events
- control scheduling

----------------------------------------
RULES
----------------------------------------

DSL functions MUST:
- return Outcome
- be side-effect free (except describing effects)
- NOT access services
- NOT contain loops or flow logic
- NOT perform validation or business logic

DSL functions are:
→ atomic
→ predictable
→ composable

Everything more complex belongs to:
    dsl.patterns.*

----------------------------------------
MENTAL MODEL
----------------------------------------

DSL = Physics
Patterns = Behavior
Commands = Orchestration
"""

from warnings import deprecated

from yakoon.base.flow.primitives.builder import create_projection
from yakoon.base.projection.model import Block, Projection
from yakoon.base.runtime import InputEvent

from .primitives import (
    AutoFocus,
    AwaitEvent,
    EmitEvent,
    EmitView,
    Outcome,
    Sleep,
    SleepUntil,
)


def out(value: Projection):
    return Outcome(value=value)


@deprecated("Use 'yield out(projection)' instead.")
def present(projection: Projection) -> Outcome:
    """
    Emit a projection to the UI.

    This represents a pure state update. It does not affect
    input routing or flow control.
    """

    return Outcome(effects=[EmitView(projection)])


@deprecated("Use 'yield out(Projection(blocks=[...]))' instead.")
def write(block: Block) -> Outcome:
    """
    Emit a single block as a projection.

    Convenience wrapper around present(), creating a minimal
    projection containing only the given block.
    """

    if not isinstance(block, Block):
        raise TypeError("write() expects a Block instance")
    projection = create_projection(blocks=[block])
    return present(projection)


def focus(projection: Projection) -> Outcome:
    """
    Emit a projection and give this flow focus.

    This marks the flow as the active receiver of subsequent
    input events. The projection itself defines how input is
    presented (e.g. structured fields or free input).
    """

    return Outcome(
        effects=[AutoFocus(), EmitView(projection)],
    )


def receive(channel: str = "default") -> Outcome:
    """
    Wait for the next input event.

    Suspends the flow until an event is received on the given
    channel. Does not emit UI or modify state.
    """

    return Outcome(control=AwaitEvent(channel))


def send(channel: str, event):
    """
    Emit an event to a channel.

    Wraps the given value as an InputEvent (if necessary) and
    sends it to the specified channel.
    """

    if not isinstance(event, InputEvent):
        event = InputEvent.from_raw(event)
    return Outcome(
        effects=[EmitEvent(channel, event)],
    )


def delay(wake_at: float) -> Outcome:
    """
    Suspend the flow for a duration.

    Pauses execution and resumes after the specified relative
    time has elapsed.
    """

    return Outcome(control=Sleep.for_duration(wake_at))


def delay_until(timestamp: float) -> Outcome:
    """
    Suspend the flow until a specific timestamp.

    Pauses execution and resumes when the given absolute time
    is reached.
    """

    return Outcome(control=SleepUntil.until(timestamp))
