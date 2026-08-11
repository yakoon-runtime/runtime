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

from typing import TYPE_CHECKING, Any, TypedDict

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.api.runtime.invoke import Call

if TYPE_CHECKING:
    from y5n.runtime.engine.nodes.tree import Tree
    from y5n.runtime.store.event.models import JsonValue, RevisionRow
    from y5n.runtime.store.event.runtime import StoreRuntime
    from y5n.runtime.store.event.store import EntityStore


class _NamespaceDict(TypedDict):
    domain: str
    kind: str
    space: str


class _KeyDict(TypedDict):
    namespace: _NamespaceDict
    id: str


def _key(raw: _KeyDict) -> Key:
    ns = raw["namespace"]
    return Key(
        namespace=Namespace(
            domain=ns["domain"],
            kind=ns["kind"],
            space=ns["space"],
        ),
        id=raw["id"],
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
    """Resolve the physical store for a call.

    Three questions, three steps (ADR-18, ADR-19):

    1. *Which pack am I?* — ``call.caller_path`` → ``tree.find()`` → the
       node's declared stores.
    2. *Which store do I want?* — ``call.store_name`` names the store the
       code asked for (``sdk.store("crm")``); with no name, the node's
       single declared store is used.
    3. *Is it declared?* — a named store must be in the node's declared
       stores. An undeclared dependency is an error, like an import whose
       module is not in the requirements (ADR-19).

    There is no default store (ADR-19). The registry maps every declared
    logical name to its ``StoreRuntime``; a node without a declared store
    resolves to None — the caller has not declared persistence.
    Ambiguity is never resolved implicitly: several declared stores
    without a name raise.
    """

    def __init__(
        self,
        tree: Tree | None,
        stores: dict[str, StoreRuntime] | None = None,
    ):
        self._tree = tree
        self._stores = stores or {}

    def resolve(self, call: Call) -> StoreRuntime | None:
        if self._tree is None:
            return None
        node = self._tree.find(call.caller_path or "/") if call.caller_path else None
        if node is None:
            return None
        if call.store_name:
            if call.store_name not in node.stores:
                raise ValueError(
                    f"Undeclared store '{call.store_name}'. "
                    "Add it to the pack's stores: declaration."
                )
            return self._stores.get(call.store_name)
        if len(node.stores) > 1:
            raise ValueError("Multiple stores declared. Please specify a store name.")
        if node.stores:
            return self._stores.get(node.stores[0])
        return None


class StoreAdapter:
    """SDK-facing ``store`` Port — resolves objects + sequencer per call.

    Every call is resolved against the calling node's declared store
    (ADR-18, ADR-19). There is no default store: a call without a
    declared store is an error — the pack has not declared persistence.
    Each resolved ``StoreRuntime`` carries its own sequencer; sequencing
    is part of the storage semantics, not a global sidecar.
    """

    def __init__(self, resolver: StoreResolver):
        self._resolver = resolver

    def _runtime_for(self, call: Call) -> StoreRuntime:
        resolved = self._resolver.resolve(call)
        if resolved is None:
            raise RuntimeError(
                f"No store bound for call at {call.caller_path!r}. "
                "The calling pack has not declared a store."
            )
        return resolved

    def _objects_for(self, call: Call) -> EntityStore:
        return self._runtime_for(call).objects

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

        from y5n.runtime.store.event.models import DomainId, EntityId, KindId, SpaceId

        k = _key(key)
        revs = await self._objects_for(call).on_load_revisions(
            domain_id=DomainId(k.namespace.domain),
            kind_id=KindId(k.namespace.kind),
            space_id=SpaceId(k.namespace.space),
            entity_id=EntityId(k.id),
            rev_gt=0,
            ts_lte=datetime.now(UTC),
        )
        out = []
        for r in revs:
            data = _revision_data(r)
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
        patch: Any,
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
            mode="and" if mode not in ("and", "or") else mode,  # type: ignore[arg-type]
            limit=limit,
        )
        return {"keys": [_key_to_dict(k) for k in keys]}

    # ------------------------
    # SEQUENCER
    # ------------------------

    async def next_id(self, call: Call, *, prefix: str) -> str:
        sequencer = self._runtime_for(call).sequencer
        if sequencer is None:
            raise RuntimeError(f"Store at {call.caller_path!r} has no sequencer.")
        return await sequencer.next_id(prefix)


def _from_iso(at_time: str | None):
    if at_time is None:
        return None
    from datetime import datetime

    return datetime.fromisoformat(at_time)


def _revision_data(revision: RevisionRow) -> JsonValue | None:
    """Extract the stored value from a revision's patch (history view).

    A revision's patch is either a list of patch operations (the first
    carries the value) or the value itself (write-only activity events).
    """
    patch = revision.patch
    if isinstance(patch, list):
        if not patch:
            return None
        first = patch[0]
        if isinstance(first, dict):
            return first.get("value")
        return first
    return patch


def _terms(indexes: list[dict] | None):
    from y5n.runtime.store.event.models import IndexTerm

    if not indexes:
        return []
    return [IndexTerm(key=t["key"], value=t["value"]) for t in indexes]


def _snapshot_hint(value: str | None):
    from y5n.runtime.store.event.models import SnapshotHint

    if value is None:
        return SnapshotHint.AUTO
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
