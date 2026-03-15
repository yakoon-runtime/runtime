class KVRenderer:

    def __init__(self, node, surface):
        self.surface = surface
        self._line_open = False

    def append(self, key: str, chunk: str):

        if key == "key":

            if self._line_open:
                self.surface.write("\n")

            self.surface.write(chunk)
            self.surface.write(": ")

            self._line_open = True

        elif key == "value":

            if not self._line_open:
                return

            self.surface.write(chunk)

    def finish(self):
        pass
