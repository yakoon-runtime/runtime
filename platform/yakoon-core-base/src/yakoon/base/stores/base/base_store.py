from abc import ABC, abstractmethod
from typing import Any

from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace


class BaseStore(ABC):
    """
    Abstract base class for all SQL-based object stores.
    Designed for use with PyPika query builders and async drivers like asyncpg or sqlite3.
    """

    @abstractmethod
    async def get_by_key(self, key: Key) -> dict | None:
        """
        Retrieve an object using a full typed Key.
        """
        pass

    @abstractmethod
    async def fetch_by_namespace(self, namespace: Namespace, *, limit: int = 100):
        """
        Return all objects within a given namespace.
        """
        pass

    @abstractmethod
    async def fetch_by_fields(
        self, *, namespace: Namespace, limit: int = 100, **fields: Any
    ) -> list[dict]:
        """
        Fetch all objects matching the given field/value pairs within a specific namespace.
        Equivalent to a WHERE clause with AND logic.
        """
        pass

    @abstractmethod
    async def save(self, obj: dict) -> None:
        """
        Persist or update the given object. Assumes 'id' or 'key' is present in the dict.
        """
        pass

    @abstractmethod
    async def delete_by_key(self, key: Key) -> None:
        """
        Delete the object associated with the given string ID.
        """
        pass
