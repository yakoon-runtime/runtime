from collections.abc import Iterable, Sequence

from yakoon.base.catalogs import AppInfo


class AppQueryBuilder:
    """
    Registry interface for routing commands to platform definitions.
    Used by the Engine to remain agnostic of structure.
    """

    def __init__(self, applications: Iterable[AppInfo]):

        by_id: dict[str, AppInfo] = {}
        shell: AppInfo | None = None

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

    def shell(self) -> AppInfo:
        return self._shell

    def ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_id.keys()))

    def all(self) -> Sequence[AppInfo]:
        return tuple(self._by_id[cid] for cid in self.ids())

    def get(self, app_id: str) -> AppInfo | None:
        return self._by_id.get(app_id)

    def has(self, app_id: str) -> bool:
        return bool(self._by_id.get(app_id, {}))

    def activatable(self) -> Sequence[AppInfo]:
        return tuple(c for c in self.all() if c.is_activatable)

    def listed(self) -> Sequence[AppInfo]:
        return tuple(c for c in self.all() if c.is_listed)

    def is_shell(self, app_id: str) -> bool:
        a = self.get(app_id)
        return bool(a and a.is_shell)

    def is_activatable(self, app_id: str) -> bool:
        a = self.get(app_id)
        return bool(a and a.is_activatable)

    def is_listed(self, app_id: str) -> bool:
        a = self.get(app_id)
        return bool(a and a.is_listed)
