from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Namespace
from y5n.runtime.store.event.backends.memory import MemoryBackend
from y5n.runtime.store.event.store import EntityStore, create_entity_store

NS = Namespace("test", "widget")


def build_store() -> EntityStore:
    return create_entity_store(MemoryBackend())


@pytest.fixture
def store() -> EntityStore:
    return build_store()
