from __future__ import annotations

from yakoon.base.projection import Projection
from yakoon.base.runtime import Container

from ...dsl import ask, receive
from ..internal.validate import apply_errors, validate

# --------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------


async def form(
    projection: Projection,
    container: Container,
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
        yield ask(projection)

        event = yield receive()

        result = validate(projection, event, container)

        if result.ok:
            yield result  # complete(result)
        else:
            projection = apply_errors(projection, result.errors)
