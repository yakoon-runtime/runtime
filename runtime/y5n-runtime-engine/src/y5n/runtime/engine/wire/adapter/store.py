"""Adapter: ``store`` port for the Runtime Bus.

Exposes the shared Event Store to the SDK as ordinary service calls.
Every pack gets the *same* store instance through this port — no more
``build_store()`` inside pack setup (ADR-17: the store belongs to the
runtime, not the pack).

The port is RPC-safe: keys and namespaces travel as strings
(``domain/kind/space#id``), results as plain dicts. The SDK models them
into typed wrappers (ADR-11).
"""

from __future__ import annotations

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call


def _key(raw: str) -> Key:
    return Key.from_str(raw)


def _namespace(raw: str) -> Namespace:
    try:
        domain, kind, space = raw.split("/")
    except ValueError as exc:
        raise ValueError(f"Invalid namespace: {raw!r}") from exc
    return Namespace(domain, kind, space)


def _key_str(key: Key) -> str:
    return str(key)


def _ns_str(ns: Namespace) -> str:
    return ns.to_str()


class StoreAdapter:
    """SDK-facing ``store`` Port — the shared Event Store + sequencer."""

    def __init__(self, objects, sequencer) -> None:
        self._objects = objects
        self._sequencer = sequencer

    # ------------------------
    # ENTITY API
    # ------------------------

    async def get(self, call: Call, *, key: str, at_time: str | None = None) -> dict:
        result = await self._objects.get(key=_key(key), at_time=_from_iso(at_time))
        return _get_result_to_dict(result)

    async def get_many(self, call: Call, *, keys: list[str]) -> list[dict]:
        results = await self._objects.get_many(keys=[_key(k) for k in keys])
        return [_get_result_to_dict(r) for r in results]

    async def history(self, call: Call, *, key: str) -> list[dict]:
        """Return the revisions of an entity — the history, not current state."""
        from datetime import UTC, datetime

        k = _key(key)
        revs = await self._objects.on_load_revisions(
            domain_id=k.namespace.domain,
            kind_id=k.namespace.kind,
            space_id=k.namespace.space,
            entity_id=k.id,
            rev_gt=0,
            ts_lte=datetime.now(UTC),
        )
        out = []
        for r in revs:
            data = r.patch[0].get("value") if isinstance(r.patch, list) else r.patch
            out.append(
                {
                    "rev": r.rev,
                    "ts": r.ts.isoformat() if r.ts else None,
                    "data": data,
                    "context": r.context,
                }
            )
        return out

    async def append(
        self,
        call: Call,
        *,
        key: str,
        patch: list[dict] | dict,
        indexes: list[dict] | None = None,
        expected_rev: int | None = None,
    ) -> dict:
        result = await self._objects.append(
            key=_key(key),
            patch=patch,
            indexes=_terms(indexes),
            expected_rev=expected_rev,
        )
        return _put_result_to_dict(result)

    async def replace(
        self,
        call: Call,
        *,
        key: str,
        doc: dict,
        indexes: list[dict] | None = None,
        expected_rev: int | None = None,
    ) -> dict:
        result = await self._objects.replace(
            key=_key(key),
            doc=doc,
            indexes=_terms(indexes),
            expected_rev=expected_rev,
        )
        return _put_result_to_dict(result)

    async def record(
        self,
        call: Call,
        *,
        key: str,
        doc: dict,
        expected_rev: int | None = None,
        context: dict | None = None,
    ) -> dict:
        result = await self._objects.record(
            key=_key(key),
            doc=doc,
            expected_rev=expected_rev,
            context=context,
        )
        return _put_result_to_dict(result)

    async def delete(
        self, call: Call, *, key: str, expected_rev: int | None = None
    ) -> dict:
        result = await self._objects.delete(key=_key(key), expected_rev=expected_rev)
        return _put_result_to_dict(result)

    # ------------------------
    # QUERY API
    # ------------------------

    async def scan(
        self,
        call: Call,
        *,
        namespace: str,
        index_key: str,
        value: str | int | float | bool | None = None,
        lo: str | int | float | bool | None = None,
        hi: str | int | float | bool | None = None,
        limit: int = 100,
        prefix: str | None = None,
        cursor: str | None = None,
    ) -> dict:
        keys, next_cursor = await self._objects.scan(
            namespace=_namespace(namespace),
            index_key=index_key,
            value=value,
            lo=lo,
            hi=hi,
            limit=limit,
            prefix=prefix,
            cursor=cursor,
        )
        return {"keys": [_key_str(k) for k in keys], "cursor": next_cursor}

    async def ensure_indexes(
        self, call: Call, *, namespace: str, specs: list[dict]
    ) -> None:
        await self._objects.ensure_indexes(
            namespace=_namespace(namespace),
            specs=_specs(specs),
        )

    async def query_index(
        self,
        call: Call,
        *,
        namespace: str,
        terms: list[dict],
        mode: str = "and",
        limit: int = 100,
    ) -> dict:
        keys, _ = await self._objects.query_index(
            namespace=_namespace(namespace),
            terms=_query_terms(terms),
            mode=mode,
            limit=limit,
        )
        return {"keys": [_key_str(k) for k in keys]}

    # ------------------------
    # SEQUENCER
    # ------------------------

    async def next_id(self, call: Call, *, prefix: str) -> int:
        shard = await self._sequencer.next_id(prefix)
        return shard


def _from_iso(at_time: str | None):
    if at_time is None:
        return None
    from datetime import datetime

    return datetime.fromisoformat(at_time)


def _terms(indexes: list[dict] | None):
    from y5n.runtime.store.event.models import IndexTerm

    if not indexes:
        return []
    return [IndexTerm(key=t["key"], value=t["value"]) for t in indexes]


def _specs(specs: list[dict]):
    from y5n.runtime.store.event.models import IndexSpec, ValueType

    return [
        IndexSpec(
            key=s["key"],
            value_type=ValueType(s["value_type"]),
            unique=bool(s.get("unique", False)),
        )
        for s in specs
    ]


def _query_terms(terms: list[dict]):
    from y5n.runtime.store.event.models import IndexQueryTerm

    return [
        IndexQueryTerm(index_key=t["index_key"], op=t["op"], value=t["value"])
        for t in terms
    ]


def _get_result_to_dict(result) -> dict:
    return {
        "key": str(result.key),
        "entity_id": str(result.entity_id),
        "data": result.data,
        "rev": result.rev,
        "as_of": result.as_of.isoformat() if result.as_of else None,
        "historical": result.historical,
    }


def _put_result_to_dict(result) -> dict:
    return {
        "entity_id": str(result.entity_id),
        "rev": result.rev,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        "snapshot_written": result.snapshot_written,
    }
