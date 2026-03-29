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
from typing import TypeGuard

from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.presentation import View, ViewHeader, v_text

from .primitives import (
    AutoFocus,
    AwaitEvent,
    AwaitInput,
    Emit,
    Outcome,
    Sleep,
    SleepUntil,
)

# --------------------------------------------------------
# OUTPUT
# --------------------------------------------------------


def show(view: View | PresenterView) -> Outcome:
    """
    Emit a view to the UI.

    Does NOT expect input.
    """
    if isinstance(view, View):
        return Outcome(effects=[Emit(view)])

    if _is_pv(view):
        return Outcome(effects=[Emit(view.view)])

    raise TypeError(f"show() expected View or PresenterView, got {type(view).__name__}")


def write(message: str) -> Outcome:
    """
    Convenience helper for emitting plain text.
    """
    return show(v_text(message))


# --------------------------------------------------------
# INPUT
# --------------------------------------------------------


def ask(view: View | PresenterView) -> Outcome:
    """
    Emit a view and wait for structured user input.

    Automatically marks the view as expecting input and focuses it.
    """

    def update_header(view: View) -> View:
        header = replace(view.header or ViewHeader(), expects_input=True)
        return replace(view, header=header)

    if isinstance(view, View):
        view = update_header(view)
        return Outcome(
            effects=[AutoFocus(), Emit(view)],
            control=AwaitInput(),
        )

    if _is_pv(view):
        view = update_header(view.view)
        return Outcome(
            effects=[AutoFocus(), Emit(view)],
            control=AwaitInput(),
        )

    raise TypeError(f"ask() expected View or PresenterView, got {type(view).__name__}")


def receive() -> Outcome:
    """
    Wait for the next event.

    Lower-level than ask():
    - no UI emitted
    - no input expectation enforced
    """
    return Outcome(control=AwaitEvent())


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


# --------------------------------------------------------
# INTERNALS
# --------------------------------------------------------


def _is_pv(v: object) -> TypeGuard[PresenterView]:
    return hasattr(v, "view")
