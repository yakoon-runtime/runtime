"""
from dataclasses import replace
from typing import TYPE_CHECKING, TypeGuard

if TYPE_CHECKING:
    from yakoon.base.capabilities.presenters import PresenterView
    from yakoon.base.runtime.input.types import InputEvent

from yakoon.base.runtime.steps import (
    AutoFocus,
    Delay,
    DelayUntil,
    Emit,
    Outcome,
    Receive,
    Show,
    WaitForInput,
)
from yakoon.base.ui.builder import v_text
from yakoon.base.ui.view import View, ViewHeader
from yakoon.platform.runtime.error import DomainError


def show(view: View | PresenterView):
    if isinstance(view, View):
        return Show(view)
    if _is_pv(view):
        return Show(view.view)
    raise TypeError(f"show() expected View or PresenterView, got {type(view).__name__}")


def ask(
    view: View | PresenterView, *, policy: str | None = None, required: bool = False
):

    def update_header(view: View) -> View:
        header = replace(view.header or ViewHeader(), expects_input=True)
        return replace(view, header=header)

    if isinstance(view, View):
        view = update_header(view)
        return Outcome(effects=[AutoFocus(), Emit(view)], control=WaitForInput())
    elif _is_pv(view):
        view = update_header(view.view)
        return Outcome(effects=[AutoFocus(), Emit(view)], control=WaitForInput())

    raise TypeError(f"ask() expected View or PresenterView, got {type(view).__name__}")


async def ask_validate(
    self,
    view,
    *,
    field: str = "result",
    policy: str | None = None,
    required: bool = False,
):
    policy_service = self.services.get(PolicyService)

    while True:
        event = yield ask(view)

        # -------------------------
        # Value holen
        # -------------------------
        value = event.get(field)

        # -------------------------
        # Required
        # -------------------------
        if required and not value:
            yield reject(field, "Pflichtfeld")
            continue

        # -------------------------
        # Policy
        # -------------------------
        if policy:
            try:
                value = policy_service.validate(policy, value)
            except DomainError as e:
                yield reject(field, e.message)
                continue

        # -------------------------
        # Erfolg
        # -------------------------
        yield Outcome(value=value)
        return


def receive(default: InputEvent | None = None, wait: bool = False):
    return Receive(default, wait)


def text(message: str):
    return Show(v_text(message))


def delay(seconds: int):
    return Delay(seconds)


def delay_until(seconds: int):
    return DelayUntil(seconds)


def _is_pv(v: object) -> TypeGuard[PresenterView]:
    return hasattr(v, "view")


class AskSpec:

    def __init__(self, view, *, policy=None, required=False):
        self.view = view
        self.policy = policy
        self.required = required
"""
