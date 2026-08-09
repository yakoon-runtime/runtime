# y5n-runtime-store

The Event Store of the Yakoon runtime.

## The principle

> **The runtime provides a store. Audit is a property of that store.**

An application does not attach PostgreSQL, manage revisions, build
context, or implement auditing. It writes:

```python
store = sdk.store()

await store.append(...)   # entity revision (with current state)
await store.record(...)   # activity event (pure history)
```

Everything else follows from the store, not from the application:

- versioned, immutable revisions
- history and point-in-time reads (`get(at_time=...)`)
- optimistic locking (`expected_rev`)
- snapshots
- **context on every revision** (actor, session, command, trace) —
  stamped by the runtime, never by the pack
- activity events (reads, denials, command outcomes) via `record()`

There is no legitimate way to change state in Yakoon without the runtime
knowing: every mutation goes through the `EntityStore`, which stamps the
context automatically. Audit is structurally enforced, not disciplinary
(ADR-17).

## A shared store, not per-pack stores

The store belongs to the runtime. Packs do not call `build_store()` —
the runtime builds one store and exposes it over the SDK `store` port, so
a command that uses the store always carries audit.

No one forces a command to use the store. But when it does, it always
audits.
