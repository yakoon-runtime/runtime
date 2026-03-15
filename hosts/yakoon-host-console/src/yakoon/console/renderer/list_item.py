class ListItemRenderer:

    def __init__(self, node, surface):
        self.surface = surface
        self._started = False
        self._first = True

    def append(self, key, chunk):

        if key != "head":
            return

        if self._first:
            self.surface.write("\n")
            self._first = False

        if not self._started:
            self.surface.write("• ")
            self._started = True

        self.surface.write(chunk)

    def finish(self):
        pass
