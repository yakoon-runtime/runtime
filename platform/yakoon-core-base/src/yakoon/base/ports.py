from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

from yakoon.base.models.stream import OutputStreaming
from yakoon.base.stores.event.entity import (
    IndexKey,
    IndexValue,
    PatchFormat,
    SnapshotHint,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from yakoon.base.plugins.plugin import PluginMeta
    from yakoon.base.runtime.commands import Request
    from yakoon.base.runtime.controllers.resources import ResourceRef
    from yakoon.base.runtime.sessions.session import Session
    from yakoon.base.stores.event.entity import (
        GetResult,
        IndexSpec,
        IndexTerm,
        JsonValue,
        PutResult,
        RetentionPolicy,
        SnapshotHint,
    )
    from yakoon.base.ui.view_spec import ViewSpec
    from yakoon.base.values import Key, Namespace
    from yakoon.platform.runtime.render.context import RenderContext


class PatchError(Exception):
    pass


class PatchStrategy(Protocol):
    """
    Pure patch semantics.
    Store uses it for:
    - applying patches on write
    - replaying patches for historical get(at_time)
    """

    @property
    def format(self) -> PatchFormat: ...

    def apply(self, current: JsonValue | None, patch: JsonValue) -> JsonValue:
        """
        Apply 'patch' to 'state' and return NEW state.
        Must not mutate 'state' in-place.
        """
        ...

    def validate(self, patch: JsonValue) -> None:
        """
        Optional: raise PatchError for invalid patches
        (e.g. too many ops, invalid paths, wrong structure).
        """
        ...

    def create_full_replace(
        self,
        *,
        current: JsonValue | None,
        new_doc: Mapping[str, JsonValue],
    ) -> JsonValue: ...

    def create_partial_update(
        self,
        *,
        current: JsonValue | None,
        fields: Mapping[str, JsonValue],
    ) -> JsonValue: ...

    def create_delete(
        self,
        *,
        current: JsonValue | None,
        fields: Sequence[str],
    ) -> JsonValue: ...


class IndexRegistry(Protocol):

    async def ensure(self, *, namespace: Namespace, specs: Sequence[IndexSpec]) -> None:
        """
        Idempotent: ensure index structures/metadata exist.
        Must NOT silently change existing specs (that is a migration).
        """
        ...

    async def list(self, *, namespace: Namespace) -> Sequence[IndexSpec]: ...


class EntityStore(Protocol):

    async def put(
        self,
        *,
        key: Key,
        patch: JsonValue,
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult:
        """
        Writes an update:
        - append revision (patch)
        - update materialized current state
        - write index terms (index-on-write)
        - optionally write snapshot (policy + hint)
        """
        ...

    async def put_doc(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...

    async def put_fields(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...

    async def delete_fields(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, Any] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...

    async def get_one(self, *, key: Key, at_time: datetime | None = None) -> GetResult:
        """
        - at_time=None => current state
        - at_time set  => reconstructed historical state (within retention window)
        """
        ...

    async def get_many(
        self,
        *,
        keys: Sequence[Key],
    ) -> list[GetResult]: ...

    async def scan(
        self,
        *,
        namespace: Namespace,
        index_key: IndexKey,
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        limit: int = 100,
        prefix: str | None = None,
        cursor: str | None = None,
    ) -> tuple[list[Key], str | None]: ...

    async def gc(self, *, namespace: Namespace, policy: RetentionPolicy) -> None:
        """
        Garbage collection / retention.
        If space_id/domain_id is None => run globally (admin job).
        """
        ...

    async def gc_global(self, *, policy: RetentionPolicy) -> None: ...


class LookupResolverService(Protocol):
    async def resolve(self, session: Session, request: Request) -> str | None: ...


class WorkflowPublic(Protocol):

    def enqueue_next(self, session: Any, batch_id: str) -> None: ...

    def start(
        self,
        session: Session,
        controller_id: str,
        command_key: str,
        *,
        enqueue_first: bool = True,
    ) -> str: ...

    def set_value(
        self, session: Session, batch_id: str, key: str, value: Any
    ) -> None: ...

    def start_with_values(
        self,
        session: Session,
        controller_id: str,
        command_key: str,
        values: Mapping[str, Any],
        *,
        enqueue_first: bool = True,
        ignore_none: bool = True,
    ) -> str: ...

    def resume_with_values(
        self,
        session: Session,
        batch_id: str,
        values: Mapping[str, Any],
        *,
        ignore_none: bool = True,
        enqueue_next: bool = True,
    ) -> None: ...

    def cancel_batch(self, session: Session, *, batch_id: str) -> None: ...


class WorkflowInternal(Protocol):
    def enqueue_next(self, session: Session, batch_id: str) -> None: ...

    def complete_input_step(
        self,
        session: Session,
        *,
        batch_id: str,
        step_id: str,
        values: Mapping[str, Any],
        ignore_none: bool = True,
    ) -> None: ...

    def complete_run_step(
        self, session: Session, *, batch_id: str, step_id: str
    ) -> None: ...

    def set_value(
        self, session: Session, batch_id: str, key: str, value: Any
    ) -> None: ...

    def fail_batch(
        self,
        session: Session,
        *,
        batch_id: str,
        code: str,
        message: str,
        command: str | None = None,
    ) -> None: ...

    def cancel_batch(self, session: Session, *, batch_id: str) -> None: ...


class RendererService(Protocol):
    async def render_view(self, ctx: RenderContext, state: str, **data) -> ViewSpec: ...


class FileLoader(Protocol):

    def load_text(
        self,
        ref: ResourceRef,
        *,
        exts: tuple[str, ...] = (".yaml", ".yml", ".json"),
        encoding: str = "utf-8",
    ) -> str: ...


class RenderEngine(Protocol):

    async def render_str(self, template_str: str, *, context: dict) -> str: ...
    async def render_any(self, obj: Any, *, context: dict) -> Any: ...


class OutputStreamService(Protocol):

    async def emit(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None: ...


class IO(Protocol):
    async def view(self, view: ViewSpec) -> None: ...


class PluginRegistry(Protocol):
    def register(self, meta: PluginMeta) -> None: ...
    def list(self) -> list[PluginMeta]: ...
