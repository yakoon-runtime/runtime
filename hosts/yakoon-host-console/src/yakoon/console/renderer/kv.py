import sys


class KVRenderer:

    def __init__(self, node):
        self._line_open = False
        self._current = None

    def append(self, key: str, chunk: str):

        # neuer key beginnt eine neue Zeile
        if key == "key":

            if self._line_open:
                sys.stdout.write("\n")

            sys.stdout.write(chunk)
            sys.stdout.write(": ")

            self._line_open = True
            self._current = "value"

        elif key == "value":

            if not self._line_open:
                return

            sys.stdout.write(chunk)

        sys.stdout.flush()
