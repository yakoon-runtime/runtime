class ActionsRenderer:

    def __init__(self, node, surface):
        self.surface = surface

    def append(self, key: str, chunk: str):
        pass

    def finish(self):
        self.surface.write("\n")
