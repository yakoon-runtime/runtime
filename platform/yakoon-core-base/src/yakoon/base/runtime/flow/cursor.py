from __future__ import annotations


class FlowCursor:

    def __init__(self, flow_factory):
        self.flow_factory = flow_factory
        self.iterator = None

    def start(self, command, request):
        self.iterator = self.flow_factory(command, request)

    async def next(self, command, request):
        if not self.iterator:
            self.start(command, request)
        return await anext(self.iterator)  # type: ignore

    async def send(self, value):
        if not self.iterator:
            raise RuntimeError("Cursor not started")
        return await self.iterator.asend(value)
