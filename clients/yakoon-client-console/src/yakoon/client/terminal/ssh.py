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

        self.reset_prompt()

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

    def notify_ready(self):
        pass  # optional

    # ------------------------
    # Prompt
    # ------------------------

    def set_prompt(self, field):
        # minimal: ignorieren oder später erweitern
        pass

    def reset_prompt(self):
        self.write("shell$ ")
