from __future__ import annotations

import asyncio
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol

from yakoon.base.models.stream import OutputStreaming
from yakoon.base.stores.event.entity import (
    IndexKey,
    IndexValue,
    PatchFormat,
    SnapshotHint,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping, Sequence

    from yakoon.base.commands.request import Request
    from yakoon.base.models.account import Account, AuthResult
    from yakoon.base.models.catalog import CommandInfo, ControllerInfo
    from yakoon.base.models.command import CommandKind
    from yakoon.base.models.input import DispatchInput
    from yakoon.base.models.key import Key
    from yakoon.base.models.ns import Namespace
    from yakoon.base.models.policy import (
        FieldPolicy,
        PolicyValidationResult,
        RawValue,
    )
    from yakoon.base.models.prompt import PromptResult
    from yakoon.base.models.view import ViewSpec
    from yakoon.base.plugins.plugin import PluginMeta
    from yakoon.base.resources.reference import ResourceRef
    from yakoon.base.runtime.session.session import Session
    from yakoon.base.stores.event.entity import (
        GetResult,
        IndexSpec,
        IndexTerm,
        JsonValue,
        PutResult,
        RetentionPolicy,
        SnapshotHint,
    )
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


class ViewSpecService(Protocol):

    def parse_spec(
        self,
        yaml_text: str,
        *,
        section_key: str | None = None,
        base_id: str | None = None,
    ) -> ViewSpec: ...


class PolicyService(Protocol):
    def register_policy(self, policy: FieldPolicy) -> None: ...
    def register_policies(self, policies: list[FieldPolicy]) -> None: ...
    def get_policy(self, key: str) -> FieldPolicy: ...
    def register_validator(self, key: str, fn) -> None: ...
    def get_validator(self, key: str) -> Callable: ...
    def register_defaults(self) -> None: ...
    def validate(self, *, policy_key: str, raw: RawValue) -> PolicyValidationResult: ...


class DialogState(StrEnum):
    IDLE = "idle"
    WAITING_WIZARD = "waiting_wizard"
    WAITING_FORM = "waiting_form"


class InputService(Protocol):

    async def ask_view(self, session: Session, field: ViewSpec) -> PromptResult: ...


class DialogService(Protocol):

    def state(self, session: Session) -> DialogState: ...
    def edge_event(self, session: Session) -> asyncio.Event: ...

    def resolve_input(self, session: Session, values: dict[str, object]) -> bool: ...
    def cancel_input(self, session: Session) -> None: ...
    def cleanup(self, session: Session) -> None: ...

    def is_waiting(self, session: Session) -> bool: ...
    def get_view(self, session: Session) -> ViewSpec: ...
    def wait_view(
        self,
        session: Session,
        *,
        view: ViewSpec,
        timeout: float | None = None,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> asyncio.Future: ...


class CommandQueueService(Protocol):
    def enqueue_commands(self, session, cmds: list[str]) -> None: ...
    def cancel_batch(self, session, batch_id: str) -> None: ...
    def next_input(self, session) -> DispatchInput | None: ...
    def has_pending(self, session) -> bool: ...


class SecretVerifier(Protocol):
    def verify(self, account: Account, secret: str) -> bool: ...


class AuthenticationService(Protocol):
    async def authenticate(
        self, namespace: Namespace, username: str, secret: str
    ) -> AuthResult: ...


class PermissionService(Protocol):

    def register_role(self, name: str, specs: list[str]) -> None: ...
    def set_bootstrap_permissions(self, session: Session): ...
    def apply_account_permissions(self, session: Session, account: Account): ...
    def can_execute(self, session: Session, perm_key: str) -> bool: ...
    def can_read(self, session: Session, perm_key: str) -> bool: ...


class AccountService(Protocol):

    async def get_by_key(self, key: Key) -> Account | None: ...
    async def get_by_username(
        self, namespace: Namespace, name: str
    ) -> Account | None: ...
    async def save(self, account: Account): ...
    async def delete_by_key(self, key: Key): ...


class CommandCatalogService(Protocol):
    def build(self) -> None: ...
    def all(self) -> tuple[CommandInfo, ...]: ...
    def for_controller(self, controller_id: str) -> Sequence[CommandInfo]: ...
    def for_controller_visible(
        self, controller_id: str, session: Session
    ) -> Sequence[CommandInfo]: ...
    def for_resolve_context(
        self,
        controller_id: str,
    ) -> tuple[CommandInfo, ...]: ...
    def for_man_entries(
        self,
        controller_id: str,
        session: Session,
        mode: str,
        kind_filter: CommandKind | None = None,
    ) -> Sequence[CommandInfo]: ...
    def resolve_info(
        self,
        controller_id: str,
        command_key: str,
    ) -> CommandInfo | None: ...


class ControllerCatalogService(Protocol):
    def ids(self) -> Sequence[str]: ...
    def all(self) -> Sequence[ControllerInfo]: ...
    def get(self, controller_id: str) -> ControllerInfo | None: ...
    def exists(self, controller_id: str) -> bool: ...
    def activatable(self) -> Sequence[ControllerInfo]: ...
    def listed(self) -> Sequence[ControllerInfo]: ...
    def shell(self) -> Sequence[ControllerInfo]: ...
    def is_shell(self, controller_id: str) -> bool: ...
    def is_activatable(self, controller_id: str) -> bool: ...
    def is_listed(self, controller_id: str) -> bool: ...


class ShardedCounterService(Protocol):
    async def next(self, prefix: str) -> str: ...


class SessionService(Protocol):
    async def delete_by_key(self, key: Key): ...
    async def get(self, key: Key) -> Session: ...
    async def get_or_create(self, key: Key, **kwargs) -> tuple[Session, bool]: ...
    async def save(self, session: Session) -> None: ...

    def release(self, key: Key) -> None: ...
    def clear(self) -> None: ...


class RendererService(Protocol):
    async def render_view(self, ctx: RenderContext, state: str, **data) -> ViewSpec: ...


class NamespaceService(Protocol):
    async def from_session(
        self, session: Session, kind: str, space: str | None
    ) -> Namespace: ...


class AuditLogService(Protocol):
    async def audit(self, msg: str): ...
    async def error(self, exc: Exception): ...
    async def permission(self, session, obj, action): ...


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


class PresenterViews(Protocol):

    async def emit(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data,
    ) -> None: ...


class PresenterInputs(Protocol):
    async def ask(self, state: str, **data) -> PromptResult: ...


class PresenterService(Protocol):
    async def create_presenter(self, resource: ResourceRef, session) -> Presenter: ...


class Presenter(Protocol):

    inputs: PresenterInputs
    views: PresenterViews


class IO(Protocol):
    async def view(self, view: ViewSpec) -> None: ...


class PluginRegistry(Protocol):
    def register(self, meta: PluginMeta) -> None: ...
    def list(self) -> list[PluginMeta]: ...
