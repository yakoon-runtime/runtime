from collections.abc import Iterable, Sequence
from typing import Any

from yakoon.base.application import Application
from yakoon.base.sources import DataRequest, DataResult, DataSource


class AppSource(DataSource):
    """
    Registry interface for applications.

    Query model:
        Exactly one selector must be provided.

    Supported selectors:
        --by-id <id>
        --all
        --listed
        --activatable
        --shell
    """

    def __init__(self, applications: Iterable[Application]):

        self._applications = applications
        self._shell: Application
        self._by_id: dict[str, Application] = {}
        self._by_name: dict[str, Application] = {}

        self._build()

        self._resolvers = {
            "by-id": self._resolve_by_id,
            "by-name": self._resolve_by_name,
            "all": self._resolve_all,
            "listed": self._resolve_listed,
            "activatable": self._resolve_activatable,
            "shell": self._resolve_shell,
        }

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def read(self, request: DataRequest) -> DataResult:

        if not request.args():
            return DataResult.invalid(reason="empty query")

        key = self._select(request)
        if isinstance(key, DataResult):
            return key

        handler = self._resolvers[key]
        return handler(request)

    # -----------------------
    # --- Selector Resolution
    # -----------------------

    def _select(self, request: DataRequest) -> str | DataResult:

        matches = [k for k in self._resolvers if request.has_option(k)]
        if not matches:
            return DataResult.invalid(reason="no selector")

        if len(matches) > 1:
            return DataResult.invalid(reason="multiple selectors")

        return matches[0]

    # ------------------------
    # Resolver Implementations
    # ------------------------

    def _resolve_by_id(self, request: DataRequest) -> DataResult:
        app_id = request.option("by-id")
        app = self._get(app_id)

        if not app:
            return DataResult.not_found(id=app_id)

        return DataResult.ok(rows=[self._to_row(app)])

    def _resolve_by_name(self, request: DataRequest) -> DataResult:
        app_name = request.option("by-name")
        app = self._get_by_name(app_name)
        if not app:
            return DataResult.not_found(name=app_name)

        return DataResult.ok(rows=[self._to_row(app)])

    def _resolve_all(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(a) for a in self._all()])

    def _resolve_listed(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(a) for a in self._all() if a.is_listed])

    def _resolve_activatable(self, request: DataRequest) -> DataResult:
        return DataResult.ok(
            rows=[self._to_row(a) for a in self._all() if a.is_activatable]
        )

    def _resolve_shell(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(self._shell)])

    # ----------------
    # Internal Helpers
    # ----------------

    def _build(self):

        by_id: dict[str, Application] = {}
        by_name: dict[str, Application] = {}
        shell: Application | None = None

        for app in self._applications:
            if app.id in by_id:
                raise ValueError(f"Duplicate application id: {app.id}")

            if app.is_shell:
                if shell is not None:
                    raise ValueError(
                        f"Duplicate shell application: {shell.id} / {app.id}"
                    )
                shell = app

            by_id[app.id] = app
            by_name[app.name] = app

        if shell is None:
            raise ValueError("No shell application found")

        self._by_name = by_name
        self._by_id = by_id
        self._shell = shell

    def _ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_id.keys()))

    def _all(self) -> Sequence[Application]:
        return tuple(self._by_id[cid] for cid in self._ids())

    def _get(self, app_id: str) -> Application | None:
        return self._by_id.get(app_id)

    def _get_by_name(self, app_name: str) -> Application | None:
        return self._by_name.get(app_name)

    def _to_row(self, app: Application) -> dict[str, Any]:
        # res = {c.id: c.resources.to_dict() for c in app.controllers}
        return {
            "id": app.id,
            "name": app.name,
            "is_shell": app.is_shell,
            "is_listed": getattr(app, "is_listed", True),
            "is_activatable": getattr(app, "is_activatable", True),
            # "resources": res,
        }
