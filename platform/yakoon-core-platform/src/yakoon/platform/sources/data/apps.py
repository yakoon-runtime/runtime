from collections.abc import Iterable, Sequence

from yakoon.base.application import Application
from yakoon.base.sources import DataRequest, DataResult, DataSource


class AppSource(DataSource):
    """
    Registry interface for routing commands to platform definitions.
    Used by the Engine to remain agnostic of structure.
    """

    def __init__(self, applications: Iterable[Application]):

        by_id: dict[str, Application] = {}
        shell: Application | None = None

        for app in applications:
            if app.id in by_id:
                raise ValueError(f"Duplicate application id: {app.id}")

            if app.is_shell:
                if shell is not None:
                    raise ValueError(
                        f"Duplicate shell application: {shell.id} / {app.id}"
                    )
                shell = app

            by_id[app.id] = app

        if shell is None:
            raise ValueError("No shell application found")

        self._by_id = by_id
        self._shell = shell

    async def read(self, request: DataRequest) -> DataResult:

        if request.has_option("by-id"):
            app = self._get(app_id=request.option("by-id"))
            if not app:
                return DataResult(rows=[])
            if request.has_option("listed") and not app.is_listed:
                return DataResult(rows=[])
            if request.has_option("activatable") and not app.is_activatable:
                return DataResult(rows=[])
            return DataResult(rows=[self._to_row(app)])

        if request.has_option("shell"):
            return DataResult(rows=[self._to_row(self._shell)])

        if request.has_option("all"):
            _to_row = self._to_row
            return DataResult(
                rows=list(_to_row(self._by_id[cid]) for cid in self._ids())
            )

        if request.has_option("activatable"):
            _to_row = self._to_row
            return DataResult(
                rows=list(_to_row(c) for c in self._all() if c.is_activatable)
            )

        if request.has_option("listed"):
            _to_row = self._to_row
            return DataResult(
                rows=list(self._to_row(c) for c in self._all() if c.is_listed)
            )

        return DataResult(rows=[])

    def _to_row(self, app) -> dict:
        return {
            "id": app.id,
            "name": getattr(app, "name", app.id),
            "is_listed": getattr(app, "is_listed", True),
            "is_activatable": getattr(app, "is_activatable", True),
        }

    def _ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_id.keys()))

    def _all(self) -> Sequence[Application]:
        return tuple(self._by_id[cid] for cid in self._ids())

    def _get(self, app_id: str) -> None | Application:
        return self._by_id.get(app_id)
