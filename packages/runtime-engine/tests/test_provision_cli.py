"""The provisioning entrypoint (``python -m y5n.runtime.engine.provision``).

The engine owns the generic factory mechanics: load ``module:attr``,
instantiate like the runtime does for ``build``, then run
``await factory.provision(config)``. Success exits 0; failures propagate
unchanged as non-zero.
"""

from __future__ import annotations

import pytest

FACTORY = "y5n.runtime.store.event.wire:EventStoreFactory"


def test_usage_error_on_wrong_argument_count():
    from y5n.runtime.engine.provision import main

    assert main(["just-the-factory"]) == 2


def test_invalid_config_json_is_a_usage_error():
    from y5n.runtime.engine.provision import main

    assert main([FACTORY, "not-json"]) == 2


def test_memory_config_is_a_successful_noop():
    from y5n.runtime.engine.provision import main

    assert main([FACTORY, '{"backend": "memory"}']) == 0


def test_unknown_factory_propagates_unchanged():
    from y5n.runtime.engine import provision

    with pytest.raises(RuntimeError):
        provision.main(["no.such.module:Factory", "{}"])


def test_instantiates_class_factories_and_calls_provision(monkeypatch):
    """Like the runtime, a class factory is instantiated before provision."""
    from y5n.runtime.engine import provision

    received: list = []

    class _RecordingFactory:
        async def provision(self, config):
            received.append(config)

    monkeypatch.setattr(provision, "load_store_factory", lambda path: _RecordingFactory)

    assert (
        provision.main([FACTORY, '{"backend": "postgres", "dsn": "env://CRM_DB"}']) == 0
    )
    assert received == [{"backend": "postgres", "dsn": "env://CRM_DB"}]
