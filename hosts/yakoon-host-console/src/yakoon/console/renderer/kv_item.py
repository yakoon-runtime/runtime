class KVItemRenderer:

    def __init__(self, node, surface):
        self.surface = surface
        self.key = node.props.get("key", "")
        self._started = False

    def append(self, key: str, chunk: str):

        if key != "value":
            return

        if not self._started:
            if self.key:
                self.surface.write(self.key)
                self.surface.write(": ")
            self._started = True

        self.surface.write(chunk)

    def finish(self):
        if self._started:
            self.surface.write("\n")
