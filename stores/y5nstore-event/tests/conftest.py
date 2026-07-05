from __future__ import annotations

import pytest
from y5n.base.naming import Namespace
from y5nstore.event.backends.memory import MemoryBackend
from y5nstore.event.batches.json_patch import JsonPatchStrategy
from y5nstore.event.store import EntityStore

NS = Namespace("test", "widget")
PATCH = JsonPatchStrategy(max_ops=50)


def build_store() -> EntityStore:
    backend = MemoryBackend()
    return EntityStore(
        on_load_current=backend.load_current,
        on_load_current_many=backend.load_current_many,
        on_load_revisions=backend.load_revisions,
        on_load_snapshot=backend.load_snapshot_at_or_before,
        on_append_revision=backend.append_revision,
        on_upsert_current=backend.upsert_current,
        on_write_snapshot=backend.write_snapshot,
        on_index_ensure=backend.index_ensure,
        on_index_list=backend.index_list,
        on_index_replace_terms=backend.index_replace_terms,
        on_index_scan=backend.index_scan,
        on_query_index=backend.query_index,
        on_gc=backend.gc,
        on_gc_global=backend.gc_global,
        writer=PATCH,
        readers={PATCH.format: PATCH},
    )


@pytest.fixture
def store() -> EntityStore:
    return build_store()
