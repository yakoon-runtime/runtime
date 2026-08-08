# ADR 17: Audit Is a Property of the Event Store

**Status:** Proposed

> **There is no audit store and no audit log — there are only events.**
>
> Every event carries a **Context**. **Domain Events** change state;
> **Activity Events** change nothing. Both live side by side in the one
> Event Store. Runtime failures stay in the runtime log.
>
> **Audit is a saved view, not a subsystem.**

## Key sentence

> **There is no audit store and no audit log — there are only events.**
> Domain Events change state; Activity Events change nothing; both live in
> one Event Store. **Audit is a saved view, not a subsystem** — the
> property that falls out of the model, not a thing to build.

## Vocabulary

The ADR replaces the term **Audit** with the concept it was trying to be.
Two terms are fixed:

> **Domain Event** — an event that changes state. It is the revision an
> Entity Store already appends when an entity is created, changed, or
> deleted (`PermissionGranted`, `ConnectionCreated`, `EndpointMoved`,
> `AccountDeleted`).

> **Activity Event** — an event that changes nothing. It records both what
> a session did (`Read`, `CommandExecuted`) and the outcome of a decision
> (`PermissionDenied`, `LoginFailed`, `Warning`) — the unifying property
> is the absence of state change, not the grammatical role. It exists
> purely as history: it never possesses a current state and is never
> materialized.

> **Context** — the envelope every event carries: `actor`, `session`,
> `command`, `trace`, `request`. Not a field named `audit` — a general
> context each event possesses.

The distinction is not *Store vs. Audit*. It is *Domain Event vs.
Activity Event*, both appended to the same store. The axis is a single
question: **does the event change the domain state or not?** — not who
caused it, not whether it is "an interaction", only whether state moved.
The same decision shows it most clearly:

```
PermissionGranted  → Domain Event   (state changed)
PermissionDenied   → Activity Event (nothing changed)
```

One decision, two events — distinguished only by whether it took effect.

## Context

### The Event Store already is the domain-event log

`EntityStore.append/replace/delete` (`store.py`) appends an immutable,
timestamped revision per mutation — that *is* a domain event stream:
append-only, versioned, replayable to any point in time (`get(at_time)`
via snapshot + revisions), and queryable through secondary indexes.

What the store does **not** record:

- **who** — `meta` exists on `append`/`delete` (`store.py:107,259`) but is
  deliberately unused (`_ = meta  # meta reserved for future use`,
  `store.py:130`);
- **what did not change** — reads, denied operations, failed logins leave
  no revision, because nothing changed;
- **correlation** — one user action may touch many entities; no command id
  ties those revisions together.

### The audit capability is mostly dead code

`capabilities/audit/service.py` wraps Python logging into rotating text
files (`y5n.audit.log`, `y5n.security.log`, `y5n.error.log`). Of its four
methods only `warning()` is wired (`wire/runtime.py:127`
`on_audit_warning=audit_service.warning`), and even that fires in a single
place (the scheduler iteration limit, `scheduler.py:162`). `audit()` and
`security()` are called nowhere. ADR-13 removed the previous audit path and
left the question open:

> *"Is audit a concern of the error command, or a separate observer of
> exceptions?"* — ADR-13, Open question 1. *"No decision yet."*

## Problem

1. **Two systems for one truth.** The durable, queryable store holds every
   state change; the flaky text-file logger holds fragments of everything
   else. Neither is the whole story, and they cannot be joined.
2. **Audit is unverdrahtet.** The capability exists but records almost
   nothing — the engine executes without an audit trail.
3. **The store cannot answer "who did what" when nothing changed.** Reads,
   denials, warnings, command outcomes are invisible in the event stream.
4. **`meta` is reserved for a future that is this.** The store already
   carries the envelope slot; it is unused.

## Decision

### 1. There is one Event Store — no audit store

Domain Events and Activity Events are entities in the **same** store,
addressed by the same four dimensions. There is no `AuditStore`, no
`audit` namespace, no second write path.

```
luma/connection/global#<id>     ← domain entities (today)
system/session/global#<key>     ← domain entities (today)
```

### 2. Domain Events vs. Activity Events

Two *kinds*, one store. The axis is one question: *does the event change
the domain state?*

| | Domain Event | Activity Event |
|---|---|---|
| changes state | yes | no |
| example | `PermissionGranted`, `ConnectionCreated`, `EndpointMoved`, `AccountDeleted` | `Read`, `CommandExecuted`, `PermissionDenied`, `LoginFailed`, `Warning` |
| exists today | yes — the store revision | no |
| writes | existing `append/replace/delete` | new — an observer at the engine boundary |
| current state | yes — materialized (rev, data) | **never** — history only |

An Activity Event carries the same envelope as a domain revision: key,
timestamp, payload, context. The difference is twofold: it is never
applied as a patch to an entity — it is written once and read back — and
it never builds a current state. It shares the domain event's append-only,
versioned, timestamped nature — it is immutable, exactly like a domain
revision — but it exists solely as history, never materialized.

### 3. Context, not audit — `meta` is generalized

The reserved `meta` on `append`/`delete` becomes the **Context** envelope,
filled by the engine at the write boundary from the already-derived
invocation context (`runtime/invocation.py:derive_invocation_context`):

```
Context
├── actor        user.id, user.name        (account)
├── session      session.key, security_context
├── command      node.path, flow.id, args  (the invocation)
├── trace        request id, origin (human/agent/scheduler), channel
└── ts           written_at (already present)
```

`meta` is not an audit field — every event possesses context. A command
that writes three entities produces three revisions, all sharing the same
`command`/`trace`, and the whole action is reconstructable from the store.

### 4. Runtime failures stay in the runtime log

A Python exception is not a domain event. `KeyError`, tracebacks, memory,
scheduler internals go to the runtime log files (the existing `error` /
`warning` loggers). The Event Store holds *fachliche* events —
`PermissionDenied`, `Read`, `Write`, `Delete`, `LoginFailed` — not
`Traceback`.

```
Runtime        ERROR, Traceback, Memory, Scheduler   → log files
Domäne         PermissionDenied, Read, Write, Delete → Event Store
```

### 5. Audit is a saved view, not a subsystem

"Audit" disappears as a concept. It is a projection over the event stream:

```
events list
events show session <key>
events show actor <name>
events show endpoint <id>
```

Same store, same index machinery, no dedicated audit feature. The command
is a normal Yakoon command like any other.

## Consequences

### Benefits

- **One truth.** Every event — state-changing or not — lives in one
  append-only, versioned, queryable store. The answer to "who did what,
  when, and why" is one query, not two systems.
- **Dead code removed.** `capabilities/audit` shrinks to a runtime-error
  logger, or disappears; ADR-13's open question is resolved: the engine
  observes, the store records.
- **`meta` finally used.** The reserved slot gets its purpose — context —
  and with it the ability to correlate multi-entity actions.
- **Activity is free.** Reads, denials, and command outcomes become
  events without new infrastructure — only an observer at the boundary.

### Trade-offs

- **Write amplification.** Every activity event is an append. Mitigated
  by the activity event never touching snapshots (it is a leaf entity)
  and by index-on-write.
- **Volume.** Activity events outnumber domain events. Retention (days,
  per kind) is the same mechanism the store already has
  (`RetentionPolicy`), not a new one.

### Simpler or more complex?

- **Model: simpler.** One store, two kinds, one envelope. "Audit" ceases
  to exist as a thing to build.
- **Runtime: a little larger.** An observer hook at the engine boundary
  (dispatch, permission, auth) that appends activity events.
- **Operator: simpler.** One query surface (`events …`) instead of log
  files plus store plus drift.

## Open questions

1. **Are Activity Events immutable and stateless, like Domain Events?**
   The bias is **yes** — they share the same append-only foundation. An
   activity event is written once, never patched, never deleted, and never
   materialized as a current state. But the store's write path is
   patch-shaped; a "write-only" append that skips the
   `upsert_current`/`replace_terms` step (the activity entity is a leaf,
   history only) needs to be spelled out.
2. **Where do Domain Events gain Context?** Today `meta` is set by
   callers who do not pass it. Decide whether the *engine* fills context
   at its store boundary (ports `OnAppend`/`OnReplace`/`OnDelete`) or the
   *services* pass it explicitly. Default bias: the engine, so packs stay
   context-free.
3. **What exactly is `CommandExecuted`?** One event per flow with outcome
   + duration, or one per effect/emission? Default bias: one per
   flow-complete, with outcome.
4. **Retention for activity events.** Same `RetentionPolicy` with
   shorter horizon, or a dedicated policy per kind? Mechanism exists;
   values are open.
5. **Name.** "Event Store" now covers both kinds. Is the store module
   (`y5n-runtime-store`) renamed, or does the vocabulary just widen?

## Implementation sketch (for later)

**Not built yet — this ADR fixes the decision, not the code.**

1. **Context on existing writes.** Fill `meta` in the engine's store
   boundary with `derive_invocation_context` fields (`actor`, `session`,
   `command`, `trace`); persist `meta` beside each revision; surface it in
   `RevisionRow`.
2. **Activity events as entities.** A new kind
   (`system/activity/global#<id>` or per-domain
   `luma/activity/global#…`) written by an observer at the engine
   boundary: dispatch (command executed/denied), permission check
   (`PermissionDenied`), auth (`LoginFailed`). A write-only append that
   never materializes current state.
3. **`events` command.** A normal command over the store: `list`
   (indexed by time/session/actor), `show <key>`. Same projection and
   rendering machinery as any pack.
4. **Runtime log keeps errors.** `capabilities/audit` reduces to
   `error`/`warning` runtime logging; `audit()` and `security()` log-file
   paths are removed.
5. **Tests.** An activity event survives an append; multi-entity command
   correlation via shared `trace`; `events show session` returns reads +
   denials + writes in order.
