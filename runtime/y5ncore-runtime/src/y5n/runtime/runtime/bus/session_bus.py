from y5n.base.clients import ClientConnection


class SessionBus:

    MAX_HISTORY = 2000

    def __init__(self):
        self._clients: set[ClientConnection] = set()
        self._history = []

    # -------------------------------------------------
    # client lifecycle
    # -------------------------------------------------

    def join(self, client: ClientConnection):
        self._clients.add(client)

        # Snapshot / Replay
        # for event in self._history:
        #    client.queue(event)

    def leave(self, client: ClientConnection):
        self._clients.discard(client)

    # -------------------------------------------------
    # broadcast
    # -------------------------------------------------

    async def broadcast(self, event):

        # reset → clear history
        if event.patch.has_reset():
            self._history.clear()

        # append history
        # self._history.append(event)
        # if len(self._history) > self.MAX_HISTORY:
        #    self._history.pop(0)

        # send to clients
        dead = []

        for client in self._clients:
            try:
                await client.emit(event)
            except Exception as e:
                print(e)
                dead.append(client)

        # cleanup broken clients
        for client in dead:
            self._clients.discard(client)
