from __future__ import annotations

import asyncio
from enum import IntEnum

from yakoon.base.capabilities.presenters.port import Presenter
from yakoon.base.ui.document import ViewSpec


class FlowState(IntEnum):
    RUNNING = 1
    WAITING = 2
    FINISHED = 3


class TickResult:
    state: FlowState
    outcome: StepOutcome | None

    def __init__(self, state, outcome):
        self.state = state
        self.outcome = outcome


class StepResult:
    def __init__(self, step):
        self.step = step


class Step:
    pass
    # async def run(self, session) -> Step: ...


class Ask(Step):

    def __init__(self, field, presenter: Presenter):
        self.presenter = presenter
        self.field = field

    async def run(self, session, request):
        view = await self.presenter.view(self.field)
        return InputRequired(view)


class Show(Step):

    def __init__(self, view: str, presenter: Presenter):
        self.view = view
        self.presenter = presenter

    async def run(self, session, request) -> Step:
        await self.presenter.present(self.view)
        return Continue()


class StepOutcome(Step):
    pass


class FlowFinished(StepOutcome):
    pass


class Continue(StepOutcome):
    pass


class Parallel(Step):

    def __init__(self, *steps):
        self.steps = steps

    async def run(self, session):
        await asyncio.gather(*(s.run(session) for s in self.steps))
        return Continue()


class InputRequired:
    view: ViewSpec

    def __init__(self, view: ViewSpec):
        self.view = view


class Form(Step):

    def __init__(self, view: str, fields: list[str]):
        self.view = view
        self.fields = fields

    async def run(self, session):
        return InputRequired(
            view=self.view,
        )
