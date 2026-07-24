from __future__ import annotations

from rich.console import Console
from rich.status import Status

_console = Console(stderr=True)


class TerminalUI:
    def __init__(self, verbose: bool = False) -> None:
        self._verbose = verbose
        self._indent = 0

    def title(self, text: str) -> None:
        _console.print(f"\n  {text}\n")

    def step(self, label: str) -> "StepContext":
        return StepContext(self, label)

    def detail(self, text: str) -> None:
        if self._verbose:
            indent = "    " * self._indent
            _console.print(f"{indent}  {text}")

    def ok(self, label: str) -> None:
        _console.print(f"  [green]✔[/green] {label}")

    def fail(self, label: str) -> None:
        _console.print(f"  [red]✘[/red] {label}")


class StepContext:
    def __init__(self, ui: TerminalUI, label: str) -> None:
        self._ui = ui
        self._label = label
        self._status: Status | None = None

    def __enter__(self) -> "StepContext":
        if not self._ui._verbose:
            self._status = _console.status(
                f"  [orange3]{self._label}...[/orange3]",
                spinner="dots",
                spinner_style="orange3",
            )
            self._status.start()
        self._ui._indent += 1
        return self

    def __exit__(self, *args) -> None:
        self._ui._indent -= 1
        success = args[0] is None
        if self._status is not None:
            self._status.stop()
        if success:
            self._ui.ok(self._label)
        else:
            self._ui.fail(self._label)

    def detail(self, text: str) -> None:
        self._ui.detail(text)
