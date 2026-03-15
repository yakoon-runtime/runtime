import random
from collections import deque

from .profiler import StreamProfiler
from .types import FinishEvent, StreamEvent, StreamEventType, TextEvent


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

        self._events: deque[StreamEvent] = deque()

        self._paused = False
        self._fast_forward = False
        self._active = False

        self._first = True
        self._sleep = 0.0

        self._profiler = StreamProfiler()

    # -------------------------------------------------
    # profiler control
    # -------------------------------------------------

    def enable_profiler(self):
        self._profiler.enabled = True
        self._profiler.reset()

    def disable_profiler(self):
        self._profiler.enabled = False

    def profiler_stats(self):
        return self._profiler.stats()

    # -------------------------------------------------
    # API used by ConsoleOutput
    # -------------------------------------------------

    def push_block(self, node_id: str, key: str, text: str):

        self._events.append(
            TextEvent(
                type=StreamEventType.TEXT,
                node=node_id,
                key=key,
                text=text,
            )
        )

        self._active = True

    def finish_block(self, node_id):

        self._events.append(
            FinishEvent(
                type=StreamEventType.FINISH,
                node=node_id,
            )
        )

        self._active = True

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

        self._events.clear()

        self._active = False
        self._fast_forward = False

    # -------------------------------------------------

    def step(self, dt):

        if self._paused:
            return

        if self._sleep > 0:
            self._sleep -= dt

            if self._profiler.enabled:
                self._profiler.sleep(dt)

            return

        processed = 0

        while self._events and processed < self.FRAME_BUDGET:

            event = self._events[0]

            # ---------------------------------------------
            # FINISH EVENT
            # ---------------------------------------------

            if isinstance(event, FinishEvent):

                self._handle_finish(event)

                if self._profiler.enabled:
                    self._profiler.event()

                processed += 1

                continue

            # ---------------------------------------------
            # TEXT EVENT
            # ---------------------------------------------

            if isinstance(event, TextEvent):

                should_pause = self._handle_text(event)

                if self._profiler.enabled:
                    self._profiler.event()

                processed += 1

                if should_pause:
                    break

                continue

            raise RuntimeError(
                f"Unexpected event in PerceptualStream: {type(event).__name__}"
            )

        # ---------------------------------------------
        # stream finished
        # ---------------------------------------------

        if self._active and not self._events:

            self._reset_internal()
            self._first = True

            if self._on_stream_finish:
                self._on_stream_finish()

    # -------------------------------------------------

    def _handle_finish(self, event: FinishEvent):

        if self._on_block_finish:
            self._on_block_finish(event.node)

        self._events.popleft()

    # -------------------------------------------------

    def _handle_text(self, event: TextEvent) -> bool:
        """
        Returns True if streaming should pause this frame.
        """

        node_id = event.node
        key = event.key
        text = event.text
        pos = event.pos

        if pos >= len(text):
            self._events.popleft()
            return False

        progress = pos / max(len(text), 1)
        step = self._step_size(progress, len(text))

        new_pos = min(len(text), pos + step)
        chunk = text[pos:new_pos]

        # natural typing: slow long words
        if " " not in chunk and len(chunk) > 12:
            new_pos = min(len(text), pos + max(4, step // 2))
            chunk = text[pos:new_pos]

        # word aware chunking
        if new_pos < len(text) and not chunk.endswith((" ", "\n", "\t")):

            rest = text[new_pos:]

            for i, c in enumerate(rest):
                if c in (" ", "\n", "\t"):
                    new_pos += i + 1
                    chunk = text[pos:new_pos]
                    break

        event.pos = new_pos

        self._on_text(node_id, key, chunk)

        if self._profiler.enabled:
            self._profiler.chunk(len(chunk))

        return self._apply_pacing(chunk)

    # -------------------------------------------------

    def _apply_pacing(self, chunk) -> bool:

        if self._fast_forward:
            return False

        pause = self._punctuation_pause(chunk)

        if pause:
            self._sleep = pause
            return True

        if self._first:
            self._first = False
            self._sleep = self.INITIAL_DELAY
        else:
            jitter = random.uniform(-self.JITTER, self.JITTER)
            self._sleep = self.FRAME_INTERVAL + jitter

        return True

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
