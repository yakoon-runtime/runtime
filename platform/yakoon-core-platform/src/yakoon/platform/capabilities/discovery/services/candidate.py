from __future__ import annotations

import secrets
import time

from yakoon.base.capabilities.discovery.lookup import LookupCandidatesPayload


class DefaultLookupCandidateStoreService:
    """
    Session-scoped short-lived store for lookup candidate lists.
    """

    def __init__(self) -> None:
        # token -> payload
        self._store: dict[str, LookupCandidatesPayload] = {}

    def put(self, payload: LookupCandidatesPayload) -> str:
        token = secrets.token_urlsafe(16)
        self._store[token] = payload
        return token

    def get(self, token: str) -> LookupCandidatesPayload | None:
        payload = self._store.get(token)
        if not payload:
            return None
        # TTL cleanup on access (simple + good enough)
        if (time.time() - payload.created_at) > payload.ttl_seconds:
            self._store.pop(token, None)
            return None
        return payload

    def delete(self, token: str) -> None:
        self._store.pop(token, None)
