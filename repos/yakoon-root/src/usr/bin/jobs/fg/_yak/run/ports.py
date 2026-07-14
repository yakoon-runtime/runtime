from typing import Protocol

from y5n.api.ports import Port


class OnFlowGetByIndexService(Protocol):
    def __call__(
        self,
        *,
        session,
        request,
    ) -> tuple[object | None, int | None]: ...


JOB_FLOW_GET = Port("jobs.flow.get", protocol=OnFlowGetByIndexService)
