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
- return Pulse
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

from y5n.runtime.api.document import to_text
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.runtime import Event

from .primitives import (
    AwaitEvent,
    Background,
    EmitEvent,
    EmitView,
    Foreground,
    Mode,
    Pulse,
    Sleep,
    SleepUntil,
    StartCommand,
    StartTask,
    Suspend,
)


def out(
    projection: dict,
    *,
    mode: Mode = "replace",
    space: str | None = None,
) -> Pulse:
    """
    Emit a transient projection to the active client.

    The projection is rendered immediately but is not
    persisted as part of the flow interaction state.

    Args:
        projection: The projection to emit.
        mode: "replace" (PatchReset + Append) or "append" (nur Append).
        space: Optional subspace name for independent job_id scoping.
    """
    return Pulse(effects=[EmitView(projection, mode=mode, space=space)])


def out_text(
    text: str,
    *,
    mode: Mode = "replace",
    space: str | None = None,
) -> Pulse:
    """
    Emit a transient text projection to the active client.

    Convenience shortcut for:
        out(to_text(...))

    Args:
        text: The text content to display.
        mode: "replace" (PatchReset + Append) or "append" (nur Append).
        space: Optional subspace name for independent job_id scoping.
    """
    return out(to_text(text), mode=mode, space=space)


def suspend() -> Pulse:
    """
    Suspend the current flow until it is explicitly resumed.

    The flow releases foreground interaction and remains
    paused at the current execution position.
    """
    return Pulse(
        control=Suspend(),
        effects=[Background()],
    )


def foreground() -> Pulse:
    """
    Move the current flow into foreground interaction.

    The flow becomes the active user interaction context.
    """
    return Pulse(
        effects=[Foreground()],
    )


def background() -> Pulse:
    """
    Remove the current flow from foreground interaction.

    The flow continues running unless blocked by a control
    such as receive(), sleep(), or suspend().
    """
    return Pulse(
        effects=[Background()],
    )


def prompt(projection: dict) -> Pulse:
    """
    Persist and emit an interactive flow projection.

    The projection becomes the current resumable interaction
    state of the flow and is automatically restored when the
    flow returns to foreground.
    """

    return Pulse(
        effects=[
            Foreground(),
            EmitView(projection, persist=True),
        ],
    )


def receive(
    channel: str | None = None,
    scope: Scope | None = None,
) -> Pulse:
    """
    Wait for the next input event.

    Without arguments — waits on USER_INPUT scope (user input).
    With a channel argument — waits on FLOW scope (flow-local channel).
    With explicit scope — uses the given scope.

    receive() intentionally has no timeout. Waiting, cancellation,
    and lifecycle management are handled by the job system,
    not by the flow.

    Usage:
        receive()                    # USER_INPUT
        receive("form.result")       # FLOW
        receive("cmd:x", scope=Scope.SESSION)  # SESSION
    """
    if scope is None:
        if channel is None:
            scope = Scope.USER_INPUT
            channel = "__user__"
        else:
            scope = Scope.FLOW
    elif channel is None:
        channel = "default"

    return Pulse(control=AwaitEvent(channel, scope=scope))


def send(channel: str, event: Event, scope: Scope = Scope.FLOW):
    """
    Emit an event to a channel.
    """
    if scope == Scope.USER_INPUT:
        raise ValueError("USER_INPUT scope cannot be used with send()")
    return Pulse(
        effects=[EmitEvent(channel, event, scope=scope)],
    )


def delay(wake_at: float) -> Pulse:
    """
    Suspend the flow for a duration.

    Pauses execution and resumes after the specified relative
    time has elapsed.
    """

    return Pulse(control=Sleep.for_duration(wake_at))


def delay_until(timestamp: float) -> Pulse:
    """
    Suspend the flow until a specific timestamp.

    Pauses execution and resumes when the given absolute time
    is reached.
    """

    return Pulse(control=SleepUntil.until(timestamp))


def view(**view_params) -> Pulse:
    """
    Send a viewport hint to the client without content.

    The client acts on view_params (e.g. clear=True) without
    rendering a projection.

    Args:
        view_params: Viewport hints (e.g. clear=True).
    """
    return Pulse(
        effects=[
            EmitView(
                {"kind": "document", "header": {"role": "info"}, "blocks": []},
                view_params=view_params or None,
            )
        ]
    )


def start_task(
    command: str, *, channel: str, scope: Scope = Scope.SESSION, **kwargs
) -> Pulse:
    """
    Start a background task.

    The task runs independently and sends its result to the given
    channel on the specified scope. The caller reads it with receive().

    Usage:
        yield start_task("python3", channel=ch, args=["-c", "print(42)"])
        result = yield receive(ch, scope=Scope.SESSION)
    """
    return Pulse(
        effects=[
            StartTask(command, channel, scope=scope, **kwargs),
        ]
    )


def start_cmd(command: str, *, channel: str, remote: str | None = None) -> Pulse:
    """
    Start a runtime command as a sub-flow.

    The sub-flow's projection output is redirected to the given
    channel (SESSION scope). The caller can read results with receive().

    Usage:
        cmd_ch = f"cmd:{uuid4().hex}"
        yield start_cmd("ls", channel=cmd_ch)
        result = yield receive(cmd_ch, scope=Scope.SESSION)
    """
    return Pulse(
        effects=[
            StartCommand(command, channel, remote=remote),
        ]
    )
