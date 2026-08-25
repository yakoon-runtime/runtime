"""SQL resources of the runtime store.

The store's physical backends ship their needed DDL as package
resources, readable from a wheel through ``importlib.resources``
(ADR-19: the factory owns its storage knowledge — the EventStore owns
its schema).
"""
