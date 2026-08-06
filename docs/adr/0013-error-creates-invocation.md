# ADR 13: An Error Creates a New Invocation — Invocation Payloads

**Status:** Accepted — implemented on the experiment branch
(`experiment/error-handling`); production migration follows.

> **Every invocation is resolved to a node and that node is executed.**
>
> An exception is not a special case. It is a boundary like the shell or the
> bus: it produces an event, the event is dispatched, a node is resolved, and
> the node's `main()` runs. The error command (`/usr/bin/err`) is an ordinary
> node — the engine knows it only as an ABI convention, never as error
> handling.
>
> This ADR is the continuation of ADR-12. ADR-12 removed the host as a type
> ("the engine knows exactly one contract: `await node.main()`"). ADR-13
> removes the last special case that survived: exceptions. After ADR-13 the
> engine has exactly one capability — *an invocation is resolved and
> dispatched to a node* — and no error-handling mode at all.

## Vocabulary

The ADR fixes one term that the error experiment revealed:

> **Payload** — the data an invocation carries, distinct from the node it
> targets.

An invocation is exactly two primary fields (ADR-12 Section 4):

```
node.path   → what is executed
args        → how it was invoked
```

ADR-13 generalizes the second field. An invocation carries a **payload**;
`args` is the payload of an ordinary command invocation, `error` is the
payload of an error invocation:

```
Invocation
    ├── node.path   → what is executed
    └── payload     → how / why it was invoked
          ├── args    (command invocation:  cd /opt)
          ├── error   (error invocation:   /usr/bin/err + exception)
          └── ...     (future: timer, webhook, signal, ...)
```

The event is the transport form; the invocation is the execution context.
**Event** describes *why* something happens (it comes from a boundary and is
transport), **Invocation** describes *under what conditions* `main()` starts
(it is established immediately before `main()` and is execution context).

```
Boundary (shell, bus, exception, timer, ...)
    ↓
Event
    ↓
Dispatch
    ↓
Resolver
    ↓
Node
    ↓
Invocation (context)
    ↓
main()
```

## Context

ADR-12 left exactly one special case in the engine: exceptions. Before
ADR-13 the error path was a second, parallel machinery:

```
Engine
 ├─ on_error_resolve (scheduler port lookup via node.ports)
 ├─ errors dict (exception type → template path)
 ├─ error templates shipped inside the engine package
 ├─ Audit calls inside error_resolve
 └─ _show_error (scheduler projects the failure itself)
```

All of it existed because an exception was treated as *a failure of the
runtime* rather than *an event that produces an invocation*. The user never
thinks "now something new starts" when a command fails — they think "my
command failed". That is the same interaction, continued.

## Problem

1. **The engine knew error handling.** It caught exceptions, resolved a
   template, and projected the failure itself. That is application
   responsibility — every pack should decide how its failures look.
2. **The error templates lived in the engine.** `error.ydf`, `usage.ydf`,
   `not_found.ydf`, ... shipped as package data inside `y5n-runtime-engine`.
   The engine owned presentation it should never know.
3. **The exception-type → template mapping was hardcoded** (`errors` dict).
   A configuration in code, owned by no pack.
4. **`node.ports` survived only for `ERROR_RESOLVE`.** The last consumer of
   the NodePorts mechanism — after every other port had moved to the Bus —
   was the error resolver.

## Decision

**An exception is a boundary. It produces an event; the event is dispatched
through the same path as every command.** The engine has no error mode. It
resolves the error node (`/usr/bin/err`) like any other command, establishes
the invocation (with the exception as payload), and executes it — in the
*same flow* when a flow already exists.

### 1. The engine translates exceptions at two boundaries

The engine catches exceptions where they can arise and immediately translates
them into an invocation — it never projects, audits, or resolves a template:

| Boundary | Where it happens | Behavior |
|----------|------------------|----------|
| **Dispatch** (node resolution) | `engine.dispatch` catches resolve/intercept failures | `error_event(error)` → recursive `dispatch` of `/usr/bin/err` — a fresh flow (no flow existed yet) |
| **Step** (command execution) | `engine.step_flow` catches generator failures | `_route_error` → the **same** flow is pointed at `/usr/bin/err` (flow id, channel, session stay; only the next step changes) |

The recursion baseline is guarded: if the error node itself cannot be
resolved (or fails), the flow terminates at a boot fallback (`out_text`).
`flow.error_depth` tracks this — it is the base case of the recursion, not
error handling.

### 2. The error node is an ordinary command

`/usr/bin/err` is a node like `ls`, `cd`, or `whoami`:

```yaml
# /usr/bin/err/.yak/yak.yml
title: Err
host: /boot/python/runtime
anonymous: true          # reachable even when the failure was PermissionDenied
entry:
  run: pack:y5n.packs.system.err:main
resources:
  ref: resource:y5n.packs.system.resources.loader:content
  error:
    default:  { path: err/error.ydf }
    denied:   { path: err/denied.ydf }
    not_found:{ path: err/not_found.ydf }
    ...
```

Its `main()` is ordinary pack logic:

```python
async def main():
    err = context.error()          # the invocation payload
    variant = _VARIANTS.get(err["type"], "default")
    resource = await runtime.resolve("/usr/bin/err", "error", {"variant": variant})
    ...
```

The command decides — which template, which language, whether to audit, log,
or recover. The engine knows none of it. `/usr/bin/err` is part of the
**System ABI**: it is a well-known path (like `/usr/bin/ls`), and what sits
behind it is swappable (`pack:company.enterprise.err:main`, a different host,
...). The engine only knows the path; the implementation is a strategy.

### 3. The invocation carries the exception as payload

The exception is serialized into the invocation context (`context.error()`):

```python
{
    "type": "NodeNotFound",
    "message": "NodeNotFound",
    "command": "does-not-exist",
    "suggestions": [...],
}
```

The SDK exposes `context.error()`. An ordinary command invocation has no
error payload (`None`); an error invocation carries it. This is the same
transport as `args` — a payload, nothing more.

### 4. The flow is the continuation, not a restart

When a command fails mid-flow, the error command runs **in the same flow** —
not as a new one. A flow describes a *connected execution*, not a successful
command:

```
Flow #42
    ├── Invocation #1  /usr/bin/cd
    ├── (exception)
    └── Invocation #2  /usr/bin/err   ← same flow, same channel
```

A new flow would force a new id, channel, session mapping, and history — the
user only wants to see `Directory '/foo' not found.` in the place where the
command's output was expected. The flow is not interrupted; its last step
changes.

### 5. The error node owns its representation

The templates moved out of the engine into the system pack (`resources/err/`).
The engine ships no `.ydf`. The exception-type → template mapping is the
command's Fachlichkeit (`_VARIANTS`), not engine configuration.

### 6. What the engine no longer does

After ADR-13 the engine does not: resolve error templates, project failures,
map exception types, audit, or catch-and-ignore. It has exactly one
capability:

> **It establishes an invocation and executes exactly one node.**

Whether that invocation came from a shell, a bus, an exception — or later a
timer or webhook — is irrelevant to the engine.

## What disappears

| Before ADR-13 | After ADR-13 |
|----------------|---------------|
| `scheduler.on_error_resolve` port + `_show_error` | gone — the scheduler only steps flows |
| `on_error_resolve` callback in `build_machine` | gone |
| `error_resolve` + `errors` dict in `runtime.py` | gone |
| Audit calls inside `error_resolve` | gone — audit becomes a concern of the error command (see Open questions) |
| Engine templates (`templates/en/*.ydf`) + package-data | moved to the system pack |
| `NodePorts` / `Container` / `ports_from` / `PortsFromHandler` / `ports/system.py` / `Port` | gone — the last `node.ports` consumer was `ERROR_RESOLVE` |
| Scheduler `except` handlers that killed or projected flows | gone — real runtime errors propagate |
| `flow.error_depth` guard | stays — the recursion baseline |

## What stays

- `dispatch(Event)` → resolve → flow — unchanged, now also the error path.
- The invocation context (ADR-12 Section 4) — unchanged; the error is an
  additional payload field.
- `flow.id`, channel, session semantics — unchanged; the error command runs
  in the same flow.
- `/usr/bin/err` is a normal command — `entry.run`, `host:`, `resources:`,
  ADR-10 resolution, all ordinary.

## Consequences

### Benefits

- **The last special case disappears.** The engine knows one path. The
  grammar of Yakoon is now: *every boundary produces an event, every event is
  dispatched, every invocation is resolved to a node, every node is
  executed.*
- **The runtime owns no error representation.** Templates, mappings, and
  presentation are pack logic — the error command's Fachlichkeit.
- **`node.ports` is gone entirely.** The NodePorts mechanism, already hollow
  after the SDK moved to the Bus, disappears with its last consumer.
- **The error strategy is swappable.** `/usr/bin/err` can be reimplemented
  per company, per host, or per deployment — the engine does not care.
- **Future boundaries are free.** `raise RestartRequested()` → `/usr/bin/restart`,
  `raise AuthenticationRequired()` → `/usr/bin/login`, a timer event →
  its node. The pattern is the same: a boundary produces an invocation.

### Trade-offs

- **The error command must be reachable.** `/usr/bin/err` is anonymous so it
  is reachable even when the failure was `PermissionDenied` — otherwise the
  error path could deny itself. This is a deliberate, documented exception,
  like the boot host.
- **Recursion needs a base case.** If the error command itself fails, the
  flow terminates at a boot fallback. That is a tiny engine-resident string —
  the single remaining engine-owned error representation.

### Is the system simpler or more complex?

- **Engine: simpler.** The engine loses the error port, the templates, the
  mapping, and the projection. Its rule becomes uniform: *dispatch events,
  establish invocations, drive flows.*
- **Scheduler: simpler.** It no longer catches exceptions to show
  projections; it steps flows and lets runtime errors propagate.
- **System-wide: simpler.** One path instead of two. The cost is the
  migration of templates into the pack and the error command's implementation.
- **Abstraction, not lines.** The net diff is roughly −750/+340 lines. The
  real gain is that "error handling" is no longer an engine concept at all —
  the same reduction ADR-12 applied to "host".

## Open questions

1. **Audit is an observer, not a projection.** Audit belonged to
   `error_resolve`. After ADR-13 the engine does not audit. Is audit a
   concern of the error command (it decides whether to log), or a separate
   observer of exceptions (an independent listener alongside the boundary)?
   The current code simply removed the audit path — no decision yet.
2. **`context.error()` vs a general payload surface.** Today `context.error()`
   is specific. A more general `context.payload()` could cover `args`, `error`,
   and future `timer`/`webhook` payloads uniformly. Not decided; the specific
   accessor is the first proof of the general idea.
3. **`flow.error_depth` as a flow operation.** `_route_error` resolves a node,
   builds an invocation, swaps the cursor, and updates the flow — all
   flow-operations. A future `flow.swap(invocation)` could move that
   mechanics into the flow, leaving the engine to say only "this flow gets a
   new invocation." Parked.
4. **Naming.** `ERROR_NODE = "/usr/bin/err"` describes the ABI convention.
   `SYSTEM_ERROR_COMMAND` would name what it is (a command path, not a node
   reference). Cosmetic; parked.

## Implementation sketch (for later)

**Done on the experiment branch:**

1. `engine.dispatch`: resolve/intercept failures → `error_event(error)` →
   recursive `dispatch` (guard: `event.error` terminates recursion).
2. `engine.step_flow`: generator failures → `_route_error` → same flow pointed
   at `/usr/bin/err` (`flow.error_depth` guards the boot fallback).
3. `Event` carries an optional `error` payload; `derive_invocation_context`
   transports it; SDK exposes `context.error()`.
4. `/usr/bin/err` command + templates moved from the engine to the system pack.
5. Removed: scheduler error path, `on_error_resolve`, `errors` dict,
   `error_resolve`, engine templates, `node.ports` / `NodePorts` / `Container`.

**Remaining / parked:**

1. Audit-as-observer decision (Open questions 1).
2. General payload surface (`context.payload()`, Open questions 2).
3. `flow.swap()` (Open questions 3).
4. `SYSTEM_ERROR_COMMAND` naming (Open questions 4).
