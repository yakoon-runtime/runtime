from __future__ import annotations

from enum import StrEnum


class SecurityContext(StrEnum):
    """The session's security context — answers *how* a session works.

    Permission grants answer "may I?". The security context answers
    "how do I work right now?". It never carries rights itself; it only
    decides whether the engine asks for a will-confirmation (elevation)
    before a ``privileged`` invocation:

    - ``normal``: privileged invocations require elevation.
    - ``temporary``: the next privileged invocation is elevated, then
      the session falls back to ``normal`` (exactly one invocation).
    - ``administrative``: a session that was consciously established as
      administrative (e.g. ``su --administrative``) — privileged
      invocations run without repeated confirmation.
    """

    NORMAL = "normal"
    TEMPORARY = "temporary"
    ADMINISTRATIVE = "administrative"
