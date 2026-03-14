class HeaderRenderer:

    def __init__(self, node, surface):
        self.surface = surface
        self._printed_role = False

    def append(self, key, chunk):

        if key == "role":
            if not self._printed_role:

                if chunk == "error":
                    self.surface.write("(Status)\n")
                elif chunk == "info":
                    self.surface.write("(Information)\n")

                self._printed_role = True

        elif key == "title":
            self.surface.write(chunk)
