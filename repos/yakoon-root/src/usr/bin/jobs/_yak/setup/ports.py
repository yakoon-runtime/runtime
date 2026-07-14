from typing import Protocol

from y5n.api.ports import Port


class OnJobsListService(Protocol):
    def __call__(self, session) -> list[tuple[int, object]]: ...


class OnFlowGetByIndexService(Protocol):
    def __call__(
        self,
        *,
        session,
        request,
    ) -> tuple[object | None, int | None]: ...


JOBS_LIST = Port("jobs.list", protocol=OnJobsListService)
JOB_FLOW_GET = Port("jobs.flow.get", protocol=OnFlowGetByIndexService)
