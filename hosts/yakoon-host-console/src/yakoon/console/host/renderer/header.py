import sys


class HeaderRenderer:

    def __init__(self, node):
        self._printed_role = False
        self._title_open = False

    def append(self, key, chunk):

        if key == "role":
            if not self._printed_role:

                if chunk == "error":
                    sys.stdout.write("(Status)\n")
                elif chunk == "info":
                    sys.stdout.write("(Information)\n")

                self._printed_role = True

        elif key == "title":
            sys.stdout.write(chunk)
            sys.stdout.flush()
            self._title_open = True

    def finish(self):

        if self._title_open:
            sys.stdout.write("\n\n")
            sys.stdout.flush()
            self._title_open = False
