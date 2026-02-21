from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

T = TypeVar("T")


class ServiceDirectory:
    """A directory for registering and retrieving services, statically or lazily."""

    def __init__(
        self, parent: ServiceDirectory | None = None, allow_override: bool = False
    ):
        """Initializes the ServiceDirectory.

        Args:
            parent: Optional parent directory for service lookup.
            allow_override: If False, prevents overriding services from the parent.
        """
        self._parent = parent
        self._allow_override = allow_override
        self._services: dict[object, object] = {}
        self._factories: dict[object, Callable[[], Awaitable[object]]] = {}

    def register_static(self, key: object, service: object) -> None:
        """Registers a static service for a given key.

        Args:
            key: The service key.
            service: The ready-to-use service instance.

        Raises:
            TypeError: If `service` is a class instead of an instance.
            ValueError: If overriding is not allowed and the key exists in the parent.
        """
        if isinstance(service, type):
            raise TypeError("Expected instance, got class. Did you forget ()?")

        if not self._allow_override and self._parent and self._parent.contains(key):
            raise ValueError(f"Service override not allowed: {key}")

        self._services[key] = service

    def register_lazy(
        self, key: object, factory: Callable[[], Awaitable[object]]
    ) -> None:
        """Registers a lazy factory for a given key.

        Args:
            key: The service key.
            factory: An async function returning a service instance.

        Raises:
            ValueError: If overriding is not allowed and the key exists in the parent.
        """
        if not self._allow_override and self._parent and self._parent.contains(key):
            raise ValueError(f"Service override not allowed: {key}")

        self._factories[key] = factory

    def contains(self, key: object) -> bool:
        """Returns True if the key is registered in this directory or its parent."""
        return key in self._services or (
            self._parent.contains(key) if self._parent else False
        )

    def fork(self, allow_override: bool = False) -> ServiceDirectory:
        """Creates a new ServiceDirectory with this directory as parent."""
        return ServiceDirectory(parent=self, allow_override=allow_override)

    def get(self, key: type[T]) -> T:
        """Retrieves the service for a given key.

        If a static service exists, it is returned. If a lazy factory is registered,
        it is awaited and cached. Otherwise, a LookupError is raised.

        Args:
            key: The service key.

        Returns:
            The service instance for the given key.

        Raises:
            KeyError: If no service is registered for the key.
        """
        try:
            if key in self._services:
                return cast(T, self._services[key])
            if key in self._factories:
                registry = self._factories[key]()
                self._services[key] = registry
                return cast(T, registry)
            if self._parent:
                return self._parent.get(key)
            raise KeyError(key)
        except KeyError as e:
            raise KeyError(f"Service not registered for key: {key!r}") from e
