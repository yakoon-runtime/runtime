from __future__ import annotations

from yakoon.base.projection.model import Projection
from yakoon.base.projection.model.block import TextBlock
from yakoon.base.runtime.input.event import InputEvent

from ...dsl import focus, receive, send

# --------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------


async def confirm(
    projection: Projection,
    channel: str,
    *,
    yes: set[str] | None = None,
    no: set[str] | None = None,
):
    """
    Confirmation interaction pattern.

    Emits a projection, activates the flow for input, and
    waits for a yes/no decision. The result is sent via the
    given channel.

    Behavior:
    - show projection and give the flow focus
    - wait for input via receive(channel)
    - normalize input to a string
    - map input to True / False using provided sets
    - repeat until valid input is received
    - emit result via send(channel, bool)

    Args:
        projection:
            The projection shown to the user (e.g. question or prompt)

        channel:
            Local channel used to emit the confirmation result

        yes:
            Accepted inputs for "yes" (default: {"y", "yes", "j", "ja"})

        no:
            Accepted inputs for "no" (default: {"n", "no", "nein"})

    Notes:
        - This pattern does not return a value.
        - Results are communicated via send/receive to remain
        consistent with the event-driven flow model.
        - The projection defines how the interaction is presented.
    """

    yes = yes or {"y", "yes", "j", "ja"}
    no = no or {"n", "no", "nein"}

    while True:
        yield focus(projection)

        event: InputEvent = yield receive()

        value = event.get("result")
        if value is None:
            raise RuntimeError("event.get() result cannot be None")

        value = value.strip().lower()
        if value in yes:
            yield send(channel, True)
            return

        if value in no:
            yield send(channel, False)
            return

        projection = _invalid_input(projection)


# --------------------------------------------------------
# INTERNALS
# --------------------------------------------------------


def _invalid_input(projection: Projection) -> Projection:
    """
    Default fallback when input is not understood.

    Keeps the pattern generic by simply appending a hint.
    """
    return Projection.create(
        blocks=[
            TextBlock(text="Bitte mit 'yes' oder 'no' antworten."),
        ]
    )
