class RuleRenderer:

    def __init__(self, node, surface):
        self.surface = surface

    def append(self, key, chunk):
        self.surface.write("-" * 60 + "\n")
