from __future__ import annotations

import sys
from typing import TextIO

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


class TerminalUI:
    def __init__(self, stream: TextIO = sys.stderr, verbose: bool = False) -> None:
        self._stream = stream
        self._verbose = verbose
        self._indent = 0

    def title(self, text: str) -> None:
        self._stream.write(f"\n  {text}\n\n")

    def step(self, label: str) -> "StepContext":
        return StepContext(self, label)

    def detail(self, text: str) -> None:
        if self._verbose:
            indent = "    " * (self._indent + 1)
            self._stream.write(f"{indent}{text}\n")

    def ok(self, label: str) -> None:
        indent = "    " * self._indent
        self._stream.write(f"{indent}{GREEN}✓{RESET} {label}\n")

    def fail(self, label: str) -> None:
        indent = "    " * self._indent
        self._stream.write(f"{indent}{RED}✖{RESET} {label}\n")

    def _push_indent(self) -> None:
        self._indent += 1

    def _pop_indent(self) -> None:
        self._indent -= 1


class StepContext:
    def __init__(self, ui: TerminalUI, label: str) -> None:
        self._ui = ui
        self._label = label

    def __enter__(self) -> "StepContext":
        self._ui._push_indent()
        return self

    def __exit__(self, *args) -> None:
        self._ui._pop_indent()
        success = args[0] is None
        if success:
            self._ui.ok(self._label)
        else:
            self._ui.fail(self._label)

    def detail(self, text: str) -> None:
        self._ui.detail(text)
