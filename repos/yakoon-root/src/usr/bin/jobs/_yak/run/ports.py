from typing import Protocol

from y5n.api.ports import Port


class OnJobsListService(Protocol):
    def __call__(self, session) -> list[tuple[int, object]]: ...


JOBS_LIST = Port("jobs.list", protocol=OnJobsListService)
