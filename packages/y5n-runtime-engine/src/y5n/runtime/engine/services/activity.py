"""Activity events (ADR-17 Phase 2).

An activity event records what a session did, asked for, or was refused —
without changing state. It is appended write-only to the Event Store:
immutable, timestamped, never materialized as a current state. Context
(actor, session, command, trace) is captured automatically by the store
from the ambient invocation; for denials at dispatch (no flow yet), it is
built explicitly from the session.

Events carry an ``all`` index term so the history is listable (ADR-17
Phase 3: ``events list``).
"""

from __future__ import annotations

import uuid

from y5n.runtime.api.naming import Namespace
from y5n.runtime.store.event.models import IndexKey, IndexSpec, IndexTerm, ValueType
from y5n.runtime.store.event.ports import OnEnsureIndexes, OnRecord


def activity_namespace() -> Namespace:
    return Namespace("system", "activity", "global")


def activity_index_spec() -> IndexSpec:
    return IndexSpec(key=IndexKey("all"), value_type=ValueType.TEXT, unique=False)


class ActivityService:
    """Writes activity events into the Event Store, write-only."""

    def __init__(self, on_record: OnRecord, on_ensure_indexes: OnEnsureIndexes):
        self._on_record = on_record
        self._on_ensure_indexes = on_ensure_indexes

    async def ensure_index(self) -> None:
        await self._on_ensure_indexes(
            namespace=activity_namespace(), specs=[activity_index_spec()]
        )

    async def record(
        self,
        *,
        kind: str,
        session,
        payload: dict | None = None,
    ) -> None:
        doc: dict = {"kind": kind}
        if payload:
            doc["payload"] = payload

        await self._on_record(
            key=activity_namespace().get_key(str(uuid.uuid4())),
            doc=doc,
            context=self._context_from_session(session),
            indexes=[IndexTerm(key=IndexKey("all"), value="1")],
        )

    @staticmethod
    def _context_from_session(session) -> dict | None:
        if session is None:
            return None

        identity = session.get_identity() if hasattr(session, "get_identity") else None
        user_name = session.user_name if hasattr(session, "user_name") else None
        security_context = (
            session.security_context if hasattr(session, "security_context") else None
        )

        return {
            "actor": {"id": str(identity) if identity else None, "name": user_name},
            "session": {
                "key": str(session.key),
                "security_context": security_context,
            },
        }
