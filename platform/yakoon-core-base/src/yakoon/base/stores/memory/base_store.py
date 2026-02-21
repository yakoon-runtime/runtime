import copy
from typing import Any

from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.stores.base.base_store import BaseStore


class MemoryStore(BaseStore):
    """
    In-memory implementation of the Store interface.
    Used for testing and ephemeral session data.
    """

    def __init__(self):
        self._rows: dict[str, dict] = {}  # key = str(Key)

    async def get_by_key(self, key: Key) -> dict | None:
        return copy.deepcopy(self._rows.get(str(key)))

    async def fetch_by_namespace(
        self, namespace: Namespace, *, limit: int = 100
    ) -> list[dict]:
        ns = namespace.to_str()
        return [
            copy.deepcopy(obj)
            for obj in self._rows.values()
            if str(obj.get("key")).startswith(ns)
        ][:limit]

    async def fetch_by_fields(
        self, *, namespace: Namespace, limit: int = 100, **fields: Any
    ) -> list[dict]:
        ns = namespace.to_str()
        return [
            copy.deepcopy(obj)
            for obj in self._rows.values()
            if str(obj.get("key")).startswith(ns)
            and all(obj.get(k) == v for k, v in fields.items())
        ][:limit]

    async def save(self, obj: dict) -> None:
        if "key" not in obj:
            raise ValueError("Missing 'key' in obj")
        if not isinstance(obj["key"], str):
            raise ValueError("'key' must be a string")
        key_str = obj["key"]
        self._rows[key_str] = copy.deepcopy(obj)

    async def delete_by_key(self, key: Key) -> None:
        self._rows.pop(str(key), None)
