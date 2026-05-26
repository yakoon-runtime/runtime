from typing import Protocol

from y5n.runtime.flow import Flow

# -------------
# --- PORTS ---
# -------------


class OnJobsList(Protocol):

    def __call__(self, session) -> list[tuple[int, Flow]]: ...


class OnFlowGetByIndex(Protocol):

    def __call__(
        self,
        *,
        session,
        request,
    ) -> tuple[Flow | None, int | None]: ...
