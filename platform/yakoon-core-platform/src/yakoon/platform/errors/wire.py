from yakoon.base.plugins.ports import OnProject

from .extract import extract_error_state
from .projector import ErrorProjector


def build_error_projector(on_project: OnProject) -> ErrorProjector:

    # --- ERROR PROJECTING ---

    error = ErrorProjector(
        on_project=on_project,
        on_extract=extract_error_state,
    )

    return error
