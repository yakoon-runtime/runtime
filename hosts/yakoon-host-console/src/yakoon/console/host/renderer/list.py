import sys


class ListRenderer:

    def __init__(self, node):
        self._line_open = False

    def append(self, key: str, chunk: str):

        if key == "head":

            if not self._line_open:
                sys.stdout.write("- ")
                self._line_open = True

            sys.stdout.write(chunk)

        elif key == "text":

            if not self._line_open:
                sys.stdout.write("  ")
                self._line_open = True

            sys.stdout.write(chunk)

        sys.stdout.flush()

    def finish(self):

        if self._line_open:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._line_open = False
