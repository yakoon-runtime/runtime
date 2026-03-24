from yakoon.base.capabilities.interaction.port import PolicyService
from yakoon.base.runtime.steps import Ask, Delay, DelayUntil, Show
from yakoon.base.ui.view import View


def show(view: View):
    return Show(view)


def ask(view: View, policies: PolicyService):
    return Ask(view, policies)


def delay(seconds: int):
    return Delay(seconds)


def delay_until(seconds: int):
    return DelayUntil(seconds)
