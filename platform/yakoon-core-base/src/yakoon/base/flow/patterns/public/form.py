from __future__ import annotations

from yakoon.base.projection import Projection

from ...dsl import focus, receive, send
from ...port import DslContext
from ..internal.validate import apply_errors, validate

# --------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------


async def form(
    context: DslContext,
    projection: Projection,
    channel_id: str,
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
        yield focus(projection)

        event = yield receive()

        result = validate(context, projection, event)
        if result.ok:
            yield send(channel_id, result.values)
            return
        else:
            projection = apply_errors(projection, result.errors)
