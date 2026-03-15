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

    def __init__(self, on_text, on_block_finish=None, on_stream_finish=None):

        self._on_text = on_text
        self._on_block_finish = on_block_finish
        self._on_stream_finish = on_stream_finish

        self._buffers = defaultdict(dict)
        self._visible = defaultdict(dict)
        self._finished_blocks = set()

        self._paused = False
        self._fast_forward = False
        self._active = False

        self._first = True
        self._sleep = 0.0

    # -------------------------------------------------
    # API used by ConsoleOutput
    # -------------------------------------------------

    def push_block(self, node_id: str, key: str, text: str):

        node_buf = self._buffers[node_id]
        node_vis = self._visible[node_id]

        node_buf[key] = node_buf.get(key, "") + text

        if key not in node_vis:
            node_vis[key] = 0

        self._active = True

    def finish_block(self, node_id: str):
        self._finished_blocks.add(node_id)

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
        self._finished_blocks.clear()

        self._active = False
        self._fast_forward = False

    # -------------------------------------------------

    def step(self, dt):

        if self._paused:
            return

        if self._sleep > 0:
            self._sleep -= dt
            return

        processed = 0

        while self._buffers and processed < self.FRAME_BUDGET:

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

            # ---------------------------------------------
            # key finished
            # ---------------------------------------------

            if pos >= len(buf):

                del node_buf[key]
                del node_vis[key]

                # block finished (no more keys)
                if not node_buf:

                    del self._buffers[node_id]
                    del self._visible[node_id]

                    if node_id in self._finished_blocks:
                        self._finished_blocks.remove(node_id)

                        if self._on_block_finish:
                            self._on_block_finish(node_id)

                continue

            # ---------------------------------------------
            # chunk calculation
            # ---------------------------------------------

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

            processed += 1

            # ---------------------------------------------
            # pacing / perceptual timing
            # ---------------------------------------------

            if not self._fast_forward:

                pause = self._punctuation_pause(chunk)

                if pause:
                    self._sleep = pause
                else:
                    if self._first:
                        self._first = False
                        self._sleep = self.INITIAL_DELAY
                    else:
                        jitter = random.uniform(-self.JITTER, self.JITTER)
                        self._sleep = self.FRAME_INTERVAL + jitter

                break

        # ---------------------------------------------
        # stream finished
        # ---------------------------------------------

        if self._active and not self._buffers:

            self._reset_internal()
            self._first = True

            if self._on_stream_finish:
                self._on_stream_finish()

    # -------------------------------------------------

    def _step_size(self, progress, length):

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
