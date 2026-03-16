from yakoon.base.interaction import ClientConnection


class SessionBus:

    MAX_HISTORY = 2000

    def __init__(self):
        self._clients: set[ClientConnection] = set()
        self._flow = None
        self._history = []

    # -------------------------------------------------
    # client lifecycle
    # -------------------------------------------------

    def join(self, client: ClientConnection):
        self._clients.add(client)

        if self._flow:
            client.set_flow_control(self._flow)

        # Snapshot / Replay
        for event in self._history:
            client.queue(event)

    def leave(self, client: ClientConnection):
        self._clients.discard(client)

    # -------------------------------------------------
    # flow control
    # -------------------------------------------------

    def set_flow_control(self, flow):
        self._flow = flow

        for client in self._clients:
            client.set_flow_control(flow)

    # -------------------------------------------------
    # broadcast
    # -------------------------------------------------

    async def broadcast(self, event):

        # reset → clear history
        if event.patch.has_reset():
            self._history.clear()

        # append history
        self._history.append(event)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)

        # send to clients
        dead = []

        for client in self._clients:
            try:
                await client.send(event)
            except Exception:
                dead.append(client)

        # cleanup broken clients
        for client in dead:
            self._clients.discard(client)
