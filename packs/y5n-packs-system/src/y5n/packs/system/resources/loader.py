"""Provides static content capabilities for the system pack.

Components reference this capability to expose documents such as
manuals and projections. The supplied path identifies a resource
relative to this package's root (the pack's ``resources/`` directory).
"""

from __future__ import annotations

from importlib.resources import files

from y5n.sdk import Resource


async def content(path: str, **params) -> Resource:
    """Provide a static content resource relative to the package root."""
    return Resource.traversable(files(__package__) / path)


__all__ = ["content"]
