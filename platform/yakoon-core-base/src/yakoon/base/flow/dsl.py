"""
DSL - Flow Primitives

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

from dataclasses import replace

from yakoon.base.projection.model import Projection, ProjectionHeader, v_text
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

# --------------------------------------------------------
# OUTPUT
# --------------------------------------------------------


def present(projection: Projection) -> Outcome:
    """
    Emit a view to the UI.

    Does NOT expect input.
    """
    return Outcome(effects=[EmitView(projection)])


def write(message: str) -> Outcome:
    """
    Convenience helper for emitting plain text.
    """
    return present(v_text(message))


# --------------------------------------------------------
# INPUT
# --------------------------------------------------------


def ask(projection: Projection) -> Outcome:
    """
    Emit a view and wait for structured user input.

    Automatically marks the view as expecting input and focuses it.
    """

    def update_header(projection: Projection) -> Projection:
        header = replace(projection.header or ProjectionHeader(), expects_input=True)
        return replace(projection, header=header)

    projection = update_header(projection)
    return Outcome(
        effects=[AutoFocus(), EmitView(projection)],
    )


# --------------------------------------------------------
# RECEIVE
# --------------------------------------------------------


def receive(channel: str = "default") -> Outcome:
    """
    Wait for the next event.

    Lower-level than ask():
    - no UI emitted
    - no input expectation enforced
    """
    return Outcome(control=AwaitEvent(channel))


# --------------------------------------------------------
# SEND
# --------------------------------------------------------


def send(channel: str, event):
    if not isinstance(event, InputEvent):
        event = InputEvent(event)
    return Outcome(
        effects=[EmitEvent(channel, event)],
        # control=YieldToScheduler(),  # entscheidend
    )


# --------------------------------------------------------
# SCHEDULING
# --------------------------------------------------------


def delay(wake_at: float) -> Outcome:
    """
    Suspend the flow for a relative duration.
    """
    return Outcome(control=Sleep.for_duration(wake_at))


def delay_until(timestamp: float) -> Outcome:
    """
    Suspend the flow until a specific point in time.
    """
    return Outcome(control=SleepUntil.until(timestamp))
