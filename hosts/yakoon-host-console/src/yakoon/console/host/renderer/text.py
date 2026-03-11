import sys


class TextRenderer:

    def __init__(self, node):
        pass

    def append(self, key, chunk):

        sys.stdout.write(chunk)
        sys.stdout.flush()

    def finish(self):
        pass
