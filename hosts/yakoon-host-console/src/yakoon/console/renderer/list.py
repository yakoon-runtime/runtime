class ListRenderer:

    def __init__(self, node, surface):
        self.surface = surface
        self._line_open = False

    def append(self, key: str, chunk: str):

        if key == "head":

            if not self._line_open:
                self.surface.write("- ")
                self._line_open = True

            self.surface.write(chunk)

        elif key == "text":

            if not self._line_open:
                self.surface.write("  ")
                self._line_open = True

            self.surface.write(chunk)

    def finish(self):
        pass
