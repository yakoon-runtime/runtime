import asyncio
import random
from collections import defaultdict, deque


class PerceptualStream:

    FRAME_INTERVAL = 1 / 60
    FRAME_BUDGET = 12

    INITIAL_DELAY = 0.06

    CHARS_START = 6
    CHARS_MID = 18
    CHARS_FAST = 48

    JITTER = 0.02

    PUNCT_PAUSE = {
        ".": 0.18,
        "!": 0.18,
        "?": 0.18,
        ":": 0.12,
        "\n": 0.08,
        "\n\n": 0.30,
    }

    # -----------------------------------------------------

    def __init__(self, on_text, on_finish=None):

        self._on_text = on_text
        self._on_finish = on_finish

        self._buffers = defaultdict(dict)
        self._visible = defaultdict(dict)

        self._queue = deque()

        self._running = False
        self._finished = False
        self._paused = False

    # -----------------------------------------------------

    def push(self, node_id: str, key: str, text: str):

        node_buf = self._buffers[node_id]
        node_vis = self._visible[node_id]

        buf = node_buf.get(key, "")
        node_buf[key] = buf + text

        if key not in node_vis:
            node_vis[key] = 0

        if not self._running:
            self._running = True
            asyncio.create_task(self._produce())

    # -----------------------------------------------------

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def finish(self):
        self._finished = True

    # -----------------------------------------------------

    def reset(self):

        self._buffers.clear()
        self._visible.clear()
        self._queue.clear()

        self._running = False
        self._finished = False

    # -----------------------------------------------------

    async def _produce(self):

        first = True

        while True:

            node_id = next(iter(self._buffers), None)
            if not node_id:
                break

            node_buf = self._buffers[node_id]
            node_vis = self._visible[node_id]

            key = next(iter(node_buf), None)
            if not key:
                del self._buffers[node_id]
                del self._visible[node_id]
                continue

            buf = node_buf[key]
            pos = node_vis[key]

            if pos >= len(buf):
                del node_buf[key]
                del node_vis[key]
                continue

            progress = pos / max(len(buf), 1)
            step = self._step_size(progress, len(buf))

            new_pos = min(len(buf), pos + step)

            chunk = buf[pos:new_pos]
            node_vis[key] = new_pos

            self._queue.append((node_id, key, chunk))

            if chunk.isspace():
                continue

            if first:
                first = False
                await asyncio.sleep(self.INITIAL_DELAY)
            else:
                jitter = random.uniform(-self.JITTER, self.JITTER)
                await asyncio.sleep(self.FRAME_INTERVAL + jitter)

        self._running = False

    # -----------------------------------------------------

    async def render_loop(self):

        while True:

            if self._paused:
                await asyncio.sleep(0.03)
                continue

            updates = 0

            while self._queue and updates < self.FRAME_BUDGET:

                node_id, key, chunk = self._queue.popleft()

                self._on_text(node_id, key, chunk)

                pause = self._punctuation_pause(chunk)
                if pause:
                    await asyncio.sleep(pause)

                updates += 1

            if self._finished and not self._queue and not self._running:
                if self._on_finish:
                    self._on_finish()

                self._finished = False

            await asyncio.sleep(self.FRAME_INTERVAL)

    # -----------------------------------------------------

    def _step_size(self, progress, length):

        if length < 80:
            return 64

        if progress < 0.15:
            return self.CHARS_START

        if progress < 0.50:
            return self.CHARS_MID

        return self.CHARS_FAST

    # -----------------------------------------------------

    def _punctuation_pause(self, chunk):

        if not chunk:
            return None

        if chunk.endswith("\n\n"):
            return self.PUNCT_PAUSE.get("\n\n")

        return self.PUNCT_PAUSE.get(chunk[-1])
