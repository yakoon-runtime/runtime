"""Provides static content capabilities for the system pack.

Components reference this loader as their resource strategy
(``resources.ref``). The host passes the capability name, the selected
variant, and the variant's parameters; the loader decides how to provide
the content. This loader serves files under this package's root.
"""

from __future__ import annotations

from importlib.resources import files

from y5n.sdk import Resource


async def content(capability: str, variant: str, **params) -> Resource:
    """Provide a static content resource relative to the package root."""
    path = params.get("path")
    if not isinstance(path, str) or not path:
        raise LookupError(f"content: variant '{variant}' requires a 'path' parameter")
    return Resource.traversable(files(__package__) / path)


__all__ = ["content"]
