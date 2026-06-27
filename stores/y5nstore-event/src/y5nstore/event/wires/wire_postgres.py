from contextlib import asynccontextmanager

from y5nstore.event.backends import PostgresBackend
from y5nstore.event.settings import StorageSettings

from ..batches.json_patch import JsonPatchStrategy
from ..runtime import StoreRuntime
from ..store import EntityStore


def build_store(settings: StorageSettings):

    # ------------------------
    # --- DEFINING BACKEND ---
    # ------------------------

    backend = PostgresBackend(settings.dsn)

    def create_store(exec):

        patch = JsonPatchStrategy(max_ops=50)

        return EntityStore(
            on_load_current=exec.load_current,
            on_load_current_many=exec.load_current_many,
            on_load_revisions=exec.load_revisions,
            on_load_snapshot=exec.load_snapshot_at_or_before,
            on_append_revision=exec.append_revision,
            on_upsert_current=exec.upsert_current,
            on_write_snapshot=exec.write_snapshot,
            on_index_ensure=exec.index_ensure,
            on_index_list=exec.index_list,
            on_index_replace_terms=exec.index_replace_terms,
            on_index_scan=exec.index_scan,
            on_query_index=exec.query_index,
            on_gc=exec.gc,
            on_gc_global=exec.gc_global,
            writer=patch,
            readers={patch.format: patch},
        )

    # ---------------------
    # --- BUILDING STORE ---
    # ---------------------

    store = create_store(backend.exec())

    # -----------------------------------
    # --- BUILDING TRANSAKTIONS STORE ---
    # -----------------------------------

    @asynccontextmanager
    async def begin_transaction():
        async with backend.transaction() as tx:
            yield create_store(tx)

    return StoreRuntime(
        objects=store,
        begin_transaction=begin_transaction,
        on_initialize=backend.initialize,
        on_shutdown=backend.shutdown,
    )
