from y5n.base.sources import DataRequest, DataResult, DataSource


class SessionSource(DataSource):
    """Query interface for active runtime sessions.

    Supported selectors:

        --list
            Returns all active sessions.

    """

    def __init__(self, host):
        self._host = host

        self._resolvers = {
            "list": self._resolve_list,
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
        rows = self._host.list_sessions()
        return DataResult.ok(rows=rows)
