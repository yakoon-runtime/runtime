from __future__ import annotations

from y5n.base.sources import DataRequest, DataResult, DataSource


class DataSourceRegistry:

    def __init__(self):
        self._sources: dict[str, DataSource] = {}

    def bind(
        self,
        source: str,
        provider: DataSource,
    ) -> None:
        if source in self._sources:
            raise RuntimeError(f"DataSource already bound: {source}")

        self._sources[source] = provider

    def resolve(self, source: str) -> DataSource | None:
        return self._sources.get(source)

    async def read(
        self,
        request: DataRequest,
    ) -> DataResult:

        provider = self.resolve(request.source)

        if not provider:
            raise LookupError(f"DataSource not found: {request.source}")

        return await provider.read(request)
