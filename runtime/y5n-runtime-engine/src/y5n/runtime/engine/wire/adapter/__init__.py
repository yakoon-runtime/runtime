"""Wire adapters — the SDK-facing ports on the Runtime Bus.

Each adapter exposes one runtime capability as ordinary service calls.
Consumers import them from this package, not from the individual modules.
"""

from .callable import CallableAdapter
from .document import DocumentAdapter
from .permission import PermissionAdapter
from .resource import ResourceAdapter
from .runtime import RuntimeAdapter
from .session import SessionAdapter
from .source import SourceReadAdapter
from .store import StoreAdapter, StoreResolver, _KeyDict

__all__ = [
    "CallableAdapter",
    "DocumentAdapter",
    "PermissionAdapter",
    "ResourceAdapter",
    "RuntimeAdapter",
    "SessionAdapter",
    "SourceReadAdapter",
    "StoreAdapter",
    "StoreResolver",
    "_KeyDict",
]
