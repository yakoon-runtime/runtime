from typing import Optional

from yakoon.base.models.key import Key
from yakoon.base.runtime.session import Session, SessionState
from yakoon.base.stores.base.base_store import BaseStore


class SessionIdentityMap:
    """
    Process-local identity map for Session instances.

    This is NOT a performance cache. Its job is to guarantee object identity:
    within a host process, the same session key always maps to the same
    Session instance (including runtime state like signals).

    Typical lifecycle:
    - get_or_create() -> puts sessions into the map
    - release() -> remove sessions on disconnect / quit / cleanup
    """

    def __init__(self) -> None:
        self._live: dict[str, Session] = {}

    def get(self, key: "Key") -> Optional["Session"]:
        """Returns the live Session instance for the given key, if present."""
        return self._live.get(str(key))

    def put(self, session: "Session") -> None:
        """Registers a live Session instance in the identity map."""
        self._live[str(session.key)] = session

    def release(self, key: "Key") -> None:
        """Removes the live Session instance for the given key (if any)."""
        self._live.pop(str(key), None)

    def clear(self) -> None:
        """Drops all live sessions from the identity map."""
        self._live.clear()


class SessionService:
    """
    Session lifecycle service.

    Responsibilities:
    - Load / create persistent SessionState via a dict-based store.
    - Hydrate a runtime Session object from that state.
    - Guarantee process-local session identity via SessionIdentityMap.

    Notes:
    - Only SessionState is persisted.
    - Session runtime (IO bindings, signals, etc.) lives only in memory and
      is preserved as long as the Session instance stays in the identity map.
    """

    def __init__(
        self, store: "BaseStore", identity_map: SessionIdentityMap | None = None
    ) -> None:
        self.store = store
        self._map = identity_map or SessionIdentityMap()

    async def get(self, key: "Key") -> Optional["Session"]:
        """
        Returns a Session for the given key if it exists (live or persisted).

        - If the session is already live in the identity map, return it.
        - Otherwise try to load state from the store and hydrate a Session.
        - If no row exists in the store, return None.
        """
        live = self._map.get(key)
        if live:
            return live

        row = await self.store.get_by_key(key)
        if not row:
            return None

        state = SessionState.from_dict(row)
        session = Session(state)
        self._map.put(session)
        return session

    async def get_or_create(self, key: "Key", **kwargs) -> tuple["Session", bool]:
        """
        Returns a live Session for the key, creating it if needed.

        Returns:
            (session, created)
            created == True if a new session was created and persisted.
        """
        existing = await self.get(key)
        if existing:
            return existing, False

        # Create new state (key is required)
        state = SessionState(key=key, **kwargs)
        session = Session(state)

        # Persist state row
        await self.store.save(state.to_dict())

        # Register live session
        self._map.put(session)
        return session, True

    async def save(self, session: "Session") -> None:
        """
        Persists the session state.

        Runtime state is not persisted.
        """
        await self.store.save(session.state.to_dict())

    def release(self, key: "Key") -> None:
        """
        Releases a live session instance from the identity map.

        Call this on disconnect / quit / end-of-connection lifecycle.
        """
        self._map.release(key)

    def clear(self) -> None:
        """
        Clears all live sessions from the identity map.

        Useful in tests or when shutting down a host process.
        """
        self._map.clear()
