from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

T = TypeVar("T")


class Container:
    """A container for registering and retrieving capability, statically or lazily."""

    def __init__(self, parent: Container | None = None, allow_override: bool = False):
        """Initializes the Container.

        Args:
            parent: Optional parent directory for capability lookup.
            allow_override: If False, prevents overriding capabilities from the parent.
        """
        self._parent = parent
        self._allow_override = allow_override
        self._container: dict[object, object] = {}
        self._factories: dict[object, Callable[[], Awaitable[object]]] = {}

    # ----------------------------------
    # BINDING
    # ----------------------------------

    def bind(self, port: object, capability: object) -> None:
        """Registers a static capability for a given port.

        Args:
            port: The port.
            capability: The ready-to-use capability instance.

        Raises:
            TypeError: If `port` is a class instead of an instance.
            ValueError: If overriding is not allowed and the port exists in the parent.
        """
        if isinstance(capability, type):
            raise TypeError("Expected instance, got class. Did you forget ()?")

        # Protect same container
        if port in self._container or port in self._factories:
            raise ValueError(f"Port already bound in this container: {port}")

        # Protect container if overwrite not allowed.
        if not self._allow_override and self._parent and self._parent.contains(port):
            raise ValueError(f"Port override not allowed: {port}")

        self._container[port] = capability

    def bind_lazy(self, port: object, factory: Callable[[], Awaitable[object]]) -> None:
        """Registers a lazy factory for a given port.

        Args:
            port: The port.
            factory: An async function returning a capability instance.

        Raises:
            ValueError: If overriding is not allowed and the port exists in the parent.
        """
        if not self._allow_override and self._parent and self._parent.contains(port):
            raise ValueError(f"Port override not allowed: {port}")

        self._factories[port] = factory

    # ----------------------------------
    # EXTENSIONS
    # ----------------------------------

    def fork(self, allow_override: bool = False) -> Container:
        """Creates a new Container with this directory as parent."""
        return Container(parent=self, allow_override=allow_override)

    def mount(self, root: Container) -> None:
        """Mountes the current container chain to a new root scope.

        This operation preserves the existing hierarchical scope chain
        while extending lookup into the attached root hierarchy.

        Intended for mounting already composed runtime spaces into
        larger runtime environments.

        Args:
            root:
                The root capability scope to attach.

        Raises:
            RuntimeError:
                If the container already has a parent scope.
        """

        if self._parent is not None:
            raise RuntimeError("Cannot attach root to container with existing parent.")

        self._parent = root

    # ----------------------------------
    # RESOLUTIONS
    # ----------------------------------

    def contains(self, port: object) -> bool:
        """Returns True if the port is registered in this directory or its parent."""
        return port in self._container or (
            self._parent.contains(port) if self._parent else False
        )

    def has(self, port: type[T]) -> bool:
        if port in self._container:
            return True
        if port in self._factories:
            return True
        if self._parent:
            return self._parent.has(port)
        return False

    def get(self, port: type[T]) -> T:
        """Retrieves the capability for a given port.

        If a static capability exists, it is returned. If a lazy factory is registered,
        it is awaited and cached. Otherwise, a LookupError is raised.

        Args:
            port: The port.

        Returns:
            The capability instance for the given port.

        Raises:
            KeyError: If no capability is registered for the port.
        """
        try:
            if port in self._container:
                return cast(T, self._container[port])
            if port in self._factories:
                registry = self._factories[port]()
                self._container[port] = registry
                return cast(T, registry)
            if self._parent:
                return self._parent.get(port)
            raise KeyError(port)
        except KeyError as e:
            raise KeyError(f"Capability not registered for port: {port!r}") from e
