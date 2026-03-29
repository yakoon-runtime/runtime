from __future__ import annotations

from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.flow.primitives.outcome import Outcome
from yakoon.base.runtime.services import ServiceDirectory

from ...dsl import ask
from ..internal.validate import apply_errors, validate

# --------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------


async def form(
    view: PresenterView,
    services: ServiceDirectory,
):
    """
    Generic form interaction pattern.

    Flow:
    - ask(view)
    - receive input
    - validate via PolicyService
    - apply errors to view (if any)
    - repeat until valid
    - return validated values

    Returns:
        dict[str, Any]
    """

    while True:
        event = yield ask(view)

        result = validate(view, event, services)

        if result.ok:
            yield Outcome(value=result)
            break

        view = apply_errors(view, result.errors)
