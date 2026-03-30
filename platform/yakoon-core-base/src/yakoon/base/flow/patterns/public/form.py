from __future__ import annotations

from yakoon.base.capabilities.presenters import PresenterView
from yakoon.base.runtime.services import ServiceDirectory

from ...dsl import ask, receive
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
        yield ask(view)

        event = yield receive()

        result = validate(view, event, services)

        if result.ok:
            yield result  # complete(result)
        else:
            view = apply_errors(view, result.errors)
