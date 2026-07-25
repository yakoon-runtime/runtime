"""Resolver — transport-free mapping of port/method to provider.

The Resolver knows nothing about how a provider is reached.
It only knows which provider exports which capabilities.

Resolution walks the tree upward from the caller's path
toward root ("/"). The closest registration wins.

This matches the classic NodePorts search: child → parent → root.
"""

from __future__ import annotations

from collections.abc import Sequence

from .messages import Placement


def _parent_path(path: str) -> str:
    """Return the parent of a tree path.

    "/usr/bin/ident" → "/usr/bin"
    "/usr/bin"       → "/usr"
    "/usr"           → "/"
    "/"              → "/"
    """
    if path in ("", "/"):
        return "/"
    parent = path.rstrip("/").rsplit("/", 1)[0]
    return parent or "/"


class Resolver:
    """Maps port/method to provider_id.

    Providers are registered at specific tree paths.
    Resolution walks upward: caller_path → parent → root.
    """

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Sequence[str]]] = {}
        self._routes: dict[str, dict[str, str]] = (
            {}
        )  # "port:method" → {path → provider_id}

    def register(
        self,
        provider_id: str,
        exports: dict[str, Sequence[str]],
        *,
        path: str = "/",
    ) -> None:
        self._providers[provider_id] = exports
        for port, methods in exports.items():
            for method in methods:
                key = f"{port}:{method}"
                if key not in self._routes:
                    self._routes[key] = {}
                self._routes[key][path] = provider_id

    def resolve(
        self,
        port: str,
        method: str,
        caller_path: str | None = None,
    ) -> str | None:
        routes = self._routes.get(f"{port}:{method}")
        if routes is None:
            return None

        caller_path = caller_path or "/"
        # Walk up from caller_path toward root
        current = caller_path
        while True:
            provider_id = routes.get(current)
            if provider_id is not None:
                return provider_id
            if current == "/":
                break
            current = _parent_path(current)

        return None

    def unregister(self, provider_id: str) -> None:
        exports = self._providers.pop(provider_id, {})
        for port, methods in exports.items():
            for method in methods:
                key = f"{port}:{method}"
                by_path = self._routes.get(key)
                if by_path is None:
                    continue
                # remove this provider from all paths it was registered at
                to_remove = [p for p, pid in by_path.items() if pid == provider_id]
                for p in to_remove:
                    del by_path[p]
                if not by_path:
                    del self._routes[key]

    def effective_path(self, caller_path: str, placement: Placement) -> str:
        """Compute the effective registration path from placement."""
        if placement == Placement.SELF:
            return caller_path
        if placement == Placement.PARENT:
            return _parent_path(caller_path)
        if placement == Placement.ROOT:
            return "/"
        return caller_path
