from typing import Any

from y5n.runtime.api.sources import DataRequest, DataResult, DataSource


class RuntimeSource(DataSource):
    """Query interface for known remote runtimes.

    Exposes the known_runtimes dict as queryable data rows.

    Supported selectors:

        --list
            Returns all known runtimes.

        --resolve <name>
            Returns the URL for a named runtime.

    """

    def __init__(self, runtimes: dict[str, str]):
        self._runtimes = runtimes

        self._resolvers = {
            "list": self._resolve_list,
            "resolve": self._resolve_by_name,
        }

    async def read(self, request: DataRequest) -> DataResult:
        if not request.args():
            return DataResult.invalid(reason="empty query")

        key = self._select(request)
        if isinstance(key, DataResult):
            return key

        handler = self._resolvers[key]
        return handler(request)

    def _select(self, request: DataRequest) -> str | DataResult:
        matches = [k for k in self._resolvers if request.has_option(k)]
        if not matches:
            return DataResult.invalid(reason="no selector")
        if len(matches) > 1:
            return DataResult.invalid(reason="multiple selectors")
        return matches[0]

    def _resolve_list(self, request: DataRequest) -> DataResult:
        rows = [{"name": name, "url": url} for name, url in self._runtimes.items()]
        return DataResult.ok(rows=rows)

    def _resolve_by_name(self, request: DataRequest) -> DataResult:
        name = request.option("resolve")
        url = self._runtimes.get(name)
        if not url:
            return DataResult.not_found(name=name)
        return DataResult.ok(rows=[{"name": name, "url": url}])
