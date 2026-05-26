from typing import Protocol

from y5n.base.nodes.request import Request
from y5n.runtime.flow.flow import Flow

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
        request: Request,
    ) -> tuple[Flow | None, int | None]: ...
