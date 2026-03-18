class FlowCursor:

    def __init__(self, flow_factory):
        self.flow_factory = flow_factory
        self.iterator = None

    def start(self, command, session, request):
        self.iterator = self.flow_factory(command, session, request)

    async def next(self, command, session, request):
        if not self.iterator:
            self.start(command, session, request)
        if self.iterator is None:
            raise RuntimeError("Cursor not started")
        # return await self.iterator.__anext__()
        return await anext(self.iterator)
