import asyncio
import random
from collections import defaultdict


class PerceptualStream:

    FRAME_INTERVAL = 1 / 15
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

    # -------------------------------------------------

    def __init__(self, on_text, on_finish=None):

        self._on_text = on_text
        self._on_finish = on_finish

        self._buffers = defaultdict(dict)
        self._visible = defaultdict(dict)

        self._paused = False
        self._fast_forward = False
        self._active = False

        self._wake = asyncio.Event()

        asyncio.create_task(self._worker())

    # -------------------------------------------------

    def push(self, node_id: str, key: str, text: str):

        node_buf = self._buffers[node_id]
        node_vis = self._visible[node_id]

        node_buf[key] = node_buf.get(key, "") + text

        if key not in node_vis:
            node_vis[key] = 0

        self._active = True
        self._wake.set()

    # -------------------------------------------------

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def fast_forward(self):
        self._fast_forward = True

    def normal_speed(self):
        self._fast_forward = False

    # -------------------------------------------------

    def _reset_internal(self):

        self._buffers.clear()
        self._visible.clear()

        self._active = False
        self._fast_forward = False

    # -------------------------------------------------

    async def _worker(self):

        first = True

        while True:

            await self._wake.wait()
            self._wake.clear()

            while self._buffers:

                if self._paused:
                    await asyncio.sleep(0.01)
                    continue

                node_id = next(iter(self._buffers))
                node_buf = self._buffers[node_id]
                node_vis = self._visible[node_id]

                key = next(iter(node_buf), None)

                if key is None:
                    del self._buffers[node_id]
                    del self._visible[node_id]
                    continue

                buf = node_buf[key]
                pos = node_vis[key]

                if pos >= len(buf):

                    del node_buf[key]
                    del node_vis[key]

                    if not node_buf:
                        del self._buffers[node_id]
                        del self._visible[node_id]

                    continue

                progress = pos / max(len(buf), 1)
                step = self._step_size(progress, len(buf))

                new_pos = min(len(buf), pos + step)
                chunk = buf[pos:new_pos]

                # natural typing: slow down long words
                if " " not in chunk and len(chunk) > 12:
                    new_pos = min(len(buf), pos + max(4, step // 2))
                    chunk = buf[pos:new_pos]

                # word-aware chunking
                if new_pos < len(buf) and not chunk.endswith((" ", "\n", "\t")):

                    rest = buf[new_pos:]

                    for i, c in enumerate(rest):
                        if c in (" ", "\n", "\t"):
                            new_pos += i + 1
                            chunk = buf[pos:new_pos]
                            break

                node_vis[key] = new_pos

                self._on_text(node_id, key, chunk)

                if not self._fast_forward:

                    pause = self._punctuation_pause(chunk)

                    if pause:
                        await asyncio.sleep(pause)

                    else:
                        if first:
                            first = False
                            await asyncio.sleep(self.INITIAL_DELAY)
                        else:
                            jitter = random.uniform(-self.JITTER, self.JITTER)
                            await asyncio.sleep(self.FRAME_INTERVAL + jitter)

            # finish transition
            if self._active:

                # clean state first
                self._reset_internal()

                # next stream should again start with typing delay
                first = True

                if self._on_finish:
                    self._on_finish()

    # -------------------------------------------------

    def _step_size(self, progress, length):

        # instant flush for short responses
        if length < 60:
            return length

        if length < 80:
            return 64

        if progress < 0.15:
            return self.CHARS_START

        if progress < 0.50:
            return self.CHARS_MID

        return self.CHARS_FAST

    # -------------------------------------------------

    def _punctuation_pause(self, chunk):

        if not chunk:
            return None

        if chunk.endswith("\n\n"):
            return self.PUNCT_PAUSE.get("\n\n")

        return self.PUNCT_PAUSE.get(chunk[-1])
