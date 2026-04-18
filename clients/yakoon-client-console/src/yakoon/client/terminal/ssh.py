import asyncio

from .base import Terminal


class SSHTerminal(Terminal):

    def __init__(self, stdin, stdout):
        self.stdin = stdin
        self.stdout = stdout
        self.on_input = None  # wird vom Client gesetzt

        self._running = True
        self._buffer = ""

    # ------------------------
    # Lifecycle
    # ------------------------
    async def run(self):
        # nichts aktiv lesen – SSH pusht Daten
        # self.reset_prompt()
        await asyncio.Future()  # block forever

    def data_received(self, data, datatype):
        self._buffer += data

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()

            if self.on_input:
                asyncio.create_task(self.on_input(line))

    async def stop(self):
        self._running = False

    # ------------------------
    # Terminal API
    # ------------------------

    def write(self, text: str):
        self.stdout.write(text)

    def new_line(self):
        self.stdout.write("\n")

    def set_prompt(self, text: str):
        self.write(text)
