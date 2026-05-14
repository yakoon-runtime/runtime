from yakoon.base.errors import ErrorState
from yakoon.platform.errors.codes import FATAL_ERROR


def extract_error_state(error: Exception) -> ErrorState:

    if error.args:
        first = error.args[0]
        if isinstance(first, ErrorState):
            return first
    return ErrorState(error.args[0] if error.args else FATAL_ERROR)
