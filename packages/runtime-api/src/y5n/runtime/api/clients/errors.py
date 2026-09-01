"""Client-facing session errors — machine-readable across the wire.

``SessionNotFound`` specializes RuntimeError so every existing handler
keeps working, while clients can react to the concrete condition without
inspecting message strings.
"""

from __future__ import annotations


class SessionNotFound(RuntimeError):
    """A retained session key no longer exists on the runtime."""

    code = "session_not_found"
