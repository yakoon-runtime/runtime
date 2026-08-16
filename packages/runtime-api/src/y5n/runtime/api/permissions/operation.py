from __future__ import annotations

from enum import StrEnum


class Operation(StrEnum):
    """Runtime operations, named after what the user does.

    The permission system stays small (`rwx` bits); the node type maps a
    runtime operation onto the required bit. Navigation (cd, ls, man, cat)
    is READ — not a separate discover/list axis.
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
