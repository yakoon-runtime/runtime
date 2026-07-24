from __future__ import annotations

import sys
from typing import TextIO


class TerminalUI:
    def __init__(self, stream: TextIO = sys.stderr) -> None:
        self._stream = stream
        self._indent = 0

    def title(self, text: str) -> None:
        self._stream.write(f"\n  {text}\n\n")

    def step(self, label: str) -> "StepContext":
        return StepContext(self, label)

    def detail(self, text: str) -> None:
        indent = "    " * (self._indent + 1)
        self._stream.write(f"{indent}  {text}\n")

    def ok(self, label: str) -> None:
        indent = "    " * self._indent
        self._stream.write(f"{indent}  ✓ {label}\n")

    def fail(self, label: str) -> None:
        indent = "    " * self._indent
        self._stream.write(f"{indent}  ✖ {label}\n")

    def _flush(self) -> None:
        self._stream.flush()


class StepContext:
    def __init__(self, ui: TerminalUI, label: str) -> None:
        self._ui = ui
        self._label = label

    def __enter__(self) -> "StepContext":
        indent = "    " * self._ui._indent
        self._ui._stream.write(f"{indent}  {self._label}...\n")
        self._ui._indent += 1
        self._ui._flush()
        return self

    def __exit__(self, *args) -> None:
        self._ui._indent -= 1

    def detail(self, text: str) -> None:
        self._ui.detail(text)

    def ok(self) -> None:
        pass
