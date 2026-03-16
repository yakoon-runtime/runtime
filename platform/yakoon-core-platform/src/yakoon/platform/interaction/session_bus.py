from yakoon.base.interaction import ClientConnection


class SessionBus:

    def __init__(self):
        self._clients: set[ClientConnection] = set()
        self._flow = None
        self._history = []

    def join(self, client: ClientConnection):
        self._clients.add(client)

        if self._flow:
            client.set_flow_control(self._flow)

        # Snapshot / Replay
        for event in self._history:
            client.queue(event)

    def leave(self, client: ClientConnection):
        self._clients.discard(client)

    def set_flow_control(self, flow):
        self._flow = flow

        for client in self._clients:
            client.set_flow_control(flow)

    async def broadcast(self, event):

        # History pflegen
        if event.patch.has_reset():
            self._history.clear()

        self._history.append(event)

        for client in tuple(self._clients):
            await client.send(event)
