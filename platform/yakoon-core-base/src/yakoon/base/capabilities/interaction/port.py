from __future__ import annotations

from asyncio import Event, Future
from collections.abc import Awaitable, Callable
from typing import Protocol

from yakoon.base.capabilities.presenters import PresentResult
from yakoon.base.runtime import Session
from yakoon.base.ui import FieldsBlock, OutputStreaming, ViewEvent, ViewSpec

from .policy import FieldPolicy, PolicyValidationResult, RawValue
from .types import DialogState


class InteractionService(Protocol):
    """
    Executes one rendered interaction document.

    Responsibilities:
      - play a view block-by-block
      - emit passive blocks immediately
      - wait on FieldsBlock(prompt)
      - validate and retry via DialogService / PolicyService
      - continue after interaction
    """

    async def play_view(
        self,
        session: Session,
        *,
        view: ViewSpec,
        stream: OutputStreaming | None = None,
    ) -> PresentResult | None: ...

    async def run_fields(
        self,
        session: Session,
        *,
        view_id: str,
        block: FieldsBlock,
        stream: OutputStreaming | None = None,
    ) -> PresentResult: ...


class DialogService(Protocol):

    def state(self, session: Session) -> DialogState: ...
    def edge_event(self, session: Session) -> Event: ...

    def resolve_input(self, session: Session, values: dict[str, object]) -> bool: ...
    def cancel_input(self, session: Session) -> None: ...
    def cleanup(self, session: Session) -> None: ...

    def is_waiting(self, session: Session) -> bool: ...
    def get_view(self, session: Session) -> ViewSpec: ...
    def get_event(self, session: Session) -> ViewEvent: ...
    def wait_view(
        self,
        session: Session,
        *,
        view: ViewSpec,
        timeout: float | None = None,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> Future: ...


class PolicyService(Protocol):
    def register_policy(self, policy: FieldPolicy) -> None: ...
    def register_policies(self, policies: list[FieldPolicy]) -> None: ...
    def get_policy(self, key: str) -> FieldPolicy: ...
    def register_validator(self, key: str, fn) -> None: ...
    def get_validator(self, key: str) -> Callable: ...
    def register_defaults(self) -> None: ...
    def validate(self, *, policy_key: str, raw: RawValue) -> PolicyValidationResult: ...
