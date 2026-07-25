"""IPC transport — connects SDK to Host.

The Host sets ``YAK_ENDPOINT`` to tell the SDK how to connect.
The SDK dispatches to the appropriate backend automatically.

Supported schemes:
  ``inprocess://``  — same-process Runtime Bus shortcut
  ``unix://path``   — Unix domain socket (planned)
  ``stdio://``      — stdin/stdout (planned)
"""

from __future__ import annotations

import os
from typing import Any

from .inprocess import invoke as _invoke_inprocess
from .inprocess import register as _register_inprocess

_MODE: str | None = None


def _detect_mode() -> str:
    global _MODE
    if _MODE is not None:
        return _MODE
    ep = os.environ.get("YAK_ENDPOINT", "")
    if ep.startswith("inprocess"):
        _MODE = "inprocess"
    elif ep.startswith("unix:"):
        _MODE = "unix"
    elif ep.startswith("stdio"):
        _MODE = "stdio"
    else:
        raise RuntimeError(
            f"YAK_ENDPOINT={ep!r} — expected inprocess://, unix://, or stdio://"
        )
    return _MODE


async def invoke(call_dict: dict[str, Any]) -> dict[str, Any]:
    mode = _detect_mode()
    if mode == "inprocess":
        return await _invoke_inprocess(call_dict)
    raise RuntimeError(f"Transport mode {mode!r} not yet implemented")


def register(
    reg_dict: dict[str, Any], methods_dict: dict[str, Any] | None = None
) -> None:
    mode = _detect_mode()
    if mode == "inprocess":
        return _register_inprocess(reg_dict, methods_dict)
    raise RuntimeError(f"Transport mode {mode!r} not yet implemented")
