"""Adapter: ``store`` port for the Runtime Bus.

Exposes the shared Event Store to the SDK as ordinary service calls.
Every pack gets the *same* store instance through this port — no more
``build_store()`` inside pack setup (ADR-17: the store belongs to the
runtime, not the pack).

The port is RPC-safe: keys travel as structured dicts
(``{"namespace": {"domain", "kind", "space"}, "id"}``) because an id may
itself contain a ``#`` (composite keys). Namespaces travel as strings,
results as plain dicts. The SDK models them into typed wrappers (ADR-11).
"""

from __future__ import annotations

from typing import Any, TypedDict

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call


class _NamespaceDict(TypedDict, total=False):
    domain: str
    kind: str
    space: str


class _KeyDict(TypedDict, total=False):
    namespace: _NamespaceDict
    id: str


def _key(raw: _KeyDict) -> Key:
    ns = raw.get("namespace") or {}
    return Key(
        namespace=Namespace(
            domain=ns.get("domain"),
            kind=ns.get("kind"),
            space=ns.get("space", "global"),
        ),
        id=raw.get("id", ""),
    )


def _key_to_dict(key: Key) -> dict[str, Any]:
    return {
        "namespace": {
            "domain": key.namespace.domain,
            "kind": key.namespace.kind,
            "space": key.namespace.space,
        },
        "id": key.id,
    }


def _namespace(raw: str) -> Namespace:
    try:
        domain, kind, space = raw.split("/")
    except ValueError as exc:
        raise ValueError(f"Invalid namespace: {raw!r}") from exc
    return Namespace(domain, kind, space)


def _index_key(raw: str):
    from y5n.runtime.store.event.models import IndexKey

    return IndexKey(raw)


class StoreResolver:
    """Resolve the physical store for a call from the calling node's declaration.

    Chain (ADR-18): ``call.caller_path`` → ``tree.find()`` → ``node.store``
    → registry → the physical store. The SDK stays dumb — ``sdk.store()``
    asks only for "a store"; the runtime derives which store from the
    component's declaration. The identity is the node, never the host
    language: a Python, Ruby, or .NET pack declaring ``store: crm`` all
    resolve to the same logical store.
    """

    def __init__(self, tree, stores: dict[str, Any] | None = None, default=None):
        self._tree = tree
        self._stores = stores or {}
        self._default = default

    def resolve(self, call: Call):
        if self._tree is None:
            return self._default
        node = self._tree.find(call.caller_path or "/") if call.caller_path else None
        profile = node.store if node is not None else None
        if profile and profile in self._stores:
            return self._stores[profile]
        return self._default


class StoreAdapter:
    """SDK-facing ``store`` Port — the shared Event Store + sequencer.

    The adapter holds the *default* store and a resolver. Every call is
    resolved against the calling node's declared store profile; a profile
    without a registered physical store falls back to the default. Today
    that is the only store — the registry is the future router boundary.
    """

    def __init__(self, objects, sequencer, resolver: StoreResolver | None = None):
        self._objects = objects
        self._sequencer = sequencer
        self._resolver = resolver or StoreResolver(tree=None, default=objects)

    def _objects_for(self, call: Call):
        return self._resolver.resolve(call)

    # ------------------------
    # ENTITY API
    # ------------------------

    async def get(
        self, call: Call, *, key: _KeyDict, at_time: str | None = None
    ) -> dict:
        result = await self._objects_for(call).get(
            key=_key(key), at_time=_from_iso(at_time)
        )
        return _get_result_to_dict(result)

    async def get_many(self, call: Call, *, keys: list[_KeyDict]) -> list[dict]:
        results = await self._objects_for(call).get_many(keys=[_key(k) for k in keys])
        return [_get_result_to_dict(r) for r in results]

    async def history(self, call: Call, *, key: _KeyDict) -> list[dict]:
        """Return the revisions of an entity — the history, not current state."""
        from datetime import UTC, datetime

        k = _key(key)
        revs = await self._objects_for(call).on_load_revisions(
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
        key: _KeyDict,
        patch: list[dict] | dict,
        indexes: list[dict] | None = None,
        snapshot_hint: str | None = None,
        meta: dict | None = None,
        expected_rev: int | None = None,
    ) -> dict:
        result = await self._objects_for(call).append(
            key=_key(key),
            patch=patch,
            indexes=_terms(indexes),
            snapshot_hint=_snapshot_hint(snapshot_hint),
            meta=meta,
            expected_rev=expected_rev,
        )
        return _put_result_to_dict(result)

    async def replace(
        self,
        call: Call,
        *,
        key: _KeyDict,
        doc: dict,
        indexes: list[dict] | None = None,
        snapshot_hint: str | None = None,
        expected_rev: int | None = None,
    ) -> dict:
        result = await self._objects_for(call).replace(
            key=_key(key),
            doc=doc,
            indexes=_terms(indexes),
            snapshot_hint=_snapshot_hint(snapshot_hint),
            expected_rev=expected_rev,
        )
        return _put_result_to_dict(result)

    async def record(
        self,
        call: Call,
        *,
        key: _KeyDict,
        doc: dict,
        expected_rev: int | None = None,
        context: dict | None = None,
        indexes: list[dict] | None = None,
    ) -> dict:
        result = await self._objects_for(call).record(
            key=_key(key),
            doc=doc,
            expected_rev=expected_rev,
            context=context,
            indexes=_terms(indexes),
        )
        return _put_result_to_dict(result)

    async def delete(
        self,
        call: Call,
        *,
        key: _KeyDict,
        meta: dict | None = None,
        expected_rev: int | None = None,
    ) -> dict:
        result = await self._objects_for(call).delete(
            key=_key(key), meta=meta, expected_rev=expected_rev
        )
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
        keys, next_cursor = await self._objects_for(call).scan(
            namespace=_namespace(namespace),
            index_key=_index_key(index_key),
            value=value,
            lo=lo,
            hi=hi,
            limit=limit,
            prefix=prefix,
            cursor=cursor,
        )
        return {"keys": [_key_to_dict(k) for k in keys], "cursor": next_cursor}

    async def ensure_indexes(
        self, call: Call, *, namespace: str, specs: list[dict]
    ) -> None:
        await self._objects_for(call).ensure_indexes(
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
        keys, _ = await self._objects_for(call).query_index(
            namespace=_namespace(namespace),
            terms=_query_terms(terms),
            mode=mode,
            limit=limit,
        )
        return {"keys": [_key_to_dict(k) for k in keys]}

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


def _snapshot_hint(value: str | None):
    from y5n.runtime.store.event.models import SnapshotHint

    if value is None:
        return None
    return SnapshotHint(value)


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
        "key": _key_to_dict(result.key),
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
