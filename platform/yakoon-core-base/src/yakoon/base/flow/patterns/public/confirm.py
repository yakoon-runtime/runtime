from __future__ import annotations

from yakoon.base.projection.model import Projection, v_text

from ...dsl import ask

# --------------------------------------------------------
# PUBLIC API
# --------------------------------------------------------


def confirm(
    projection: Projection,
    *,
    yes: set[str] | None = None,
    no: set[str] | None = None,
):
    """
    Generic confirmation pattern.

    Flow:
    - ask(projection)
    - wait for user input
    - map input to True / False
    - repeat until valid

    Args:
        projection:
            The projection shown to the user (question, prompt, etc.)

        yes:
            Accepted inputs for "yes" (default: {"y", "yes"})

        no:
            Accepted inputs for "no" (default: {"n", "no"})

    Returns:
        bool
    """

    yes = yes or {"y", "yes", "1", "j", "ja"}
    no = no or {"n", "no", "0", "nein"}

    while True:
        event = yield ask(projection)

        if not event:
            continue

        value = str(event).strip().lower()

        if value in yes:
            return True

        if value in no:
            return False

        # fallback: ask again with hint
        projection = _invalid_input(projection)


# --------------------------------------------------------
# INTERNALS
# --------------------------------------------------------


def _invalid_input(projection: Projection) -> Projection:
    """
    Default fallback when input is not understood.

    Keeps the pattern generic by simply appending a hint.
    """
    return v_text("Bitte mit 'yes' oder 'no' antworten.")
