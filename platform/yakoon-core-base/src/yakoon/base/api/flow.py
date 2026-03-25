from typing import TypeGuard

from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.runtime.input.types import InputEvent
from yakoon.base.runtime.steps import Ask, Delay, DelayUntil, Receive, Show
from yakoon.base.ui.builder import v_text
from yakoon.base.ui.view import View


def show(view: View | PresenterView):
    if isinstance(view, View):
        return Show(view)
    if _is_pv(view):
        return Show(view.view)
    raise TypeError(f"show() expected View or PresenterView, got {type(view).__name__}")


def ask(view: View | PresenterView):
    if isinstance(view, View):
        return Ask(view)
    if _is_pv(view):
        return Ask(view.view)
    raise TypeError(f"ask() expected View or PresenterView, got {type(view).__name__}")


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
