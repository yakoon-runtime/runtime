class ActionRenderer:

    def __init__(self, node, surface):
        self.surface = surface

    def append(self, key: str, chunk: str):
        self.surface.write(chunk)

    def finish(self):
        self.surface.write("\n")
