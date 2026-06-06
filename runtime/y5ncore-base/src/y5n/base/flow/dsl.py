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

from y5n.base.projection import Projection, to_text
from y5n.base.runtime import Event

from .primitives import (
    AwaitEvent,
    Background,
    EmitEvent,
    EmitView,
    Foreground,
    Outcome,
    Sleep,
    SleepUntil,
    Suspend,
    TaskHandle,
)


def out(value: Projection) -> Outcome:
    """
    Emit a transient projection to the active client.

    The projection is rendered immediately but is not
    persisted as part of the flow interaction state.
    """
    return Outcome(value=value)


def out_text(text: str) -> Outcome:
    """
    Emit a transient text projection to the active client.

    Convenience shortcut for:
        out(to_text(...))

    The emitted text is rendered immediately but is not
    persisted as part of the flow interaction state.
    """
    return out(to_text(text))


def suspend() -> Outcome:
    """
    Suspend the current flow until it is explicitly resumed.

    The flow releases foreground interaction and remains
    paused at the current execution position.
    """
    return Outcome(
        control=Suspend(),
        effects=[Background()],
    )


def foreground() -> Outcome:
    """
    Move the current flow into foreground interaction.

    The flow becomes the active user interaction context.
    """
    return Outcome(
        effects=[Foreground()],
    )


def background() -> Outcome:
    """
    Remove the current flow from foreground interaction.

    The flow continues running unless blocked by a control
    such as receive(), sleep(), or suspend().
    """
    return Outcome(
        effects=[Background()],
    )


def prompt(projection: Projection) -> Outcome:
    """
    Persist and emit an interactive flow projection.

    The projection becomes the current resumable interaction
    state of the flow and is automatically restored when the
    flow returns to foreground.
    """

    return Outcome(
        effects=[
            Foreground(),
            EmitView(projection, persist=True),
        ],
    )


def receive(channel: str = "default") -> Outcome:
    """
    Wait for the next input event.

    Suspends the flow until an event is received on the given
    channel. Does not emit UI or modify state.
    """

    return Outcome(control=AwaitEvent(channel))


def send(channel: str, event: Event):
    """
    Emit an event to a channel.
    """
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


def run_task(command: str, **kwargs) -> TaskHandle:
    """
    Create a TaskHandle for a background task.

    Returns a TaskHandle that can be yielded to start the task.
    The task's result arrives via receive(task.channel).

    Usage:
        task = run_task("sleep", seconds=5)
        yield task
        result = yield receive(task.channel)
    """
    return TaskHandle(command=command, **kwargs)
