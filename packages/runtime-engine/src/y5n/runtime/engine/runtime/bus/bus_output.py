class BusOutput:

    def __init__(self, bus):
        self._bus = bus

    def set_flow_control(self, flow):
        self._bus.set_flow_control(flow)

    async def view(self, event):
        await self._bus.broadcast(event)
