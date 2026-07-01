# Architecture Decisions

> Rule of thumb: If you'd have to explain it to someone else → put it here.
> Document: What? And Why?

---

## 2026-06-29 — Interaction is Flow

Interactive dialogs (forms, wizards, input prompts) are not a separate subsystem. They are regular flows that pause on `AwaitEvent` and produce a `Request` via `Context(control=Continue(...))`.

**Key insight:** The `FormRenderer` does not render — it collects input. The form is a projection. The interaction is a flow.

**What this enables:**
- Dialog suspension (`bg`/`fg`) uses the existing flow scheduler — no dialog manager needed
- Pipeline chaining works for forms as for any command
- Agents, humans, and remote runtimes all interact via the same `Request`/`Continue` mechanism
- Multiple concurrent dialogs are independent flows with independent state

## 2026-05-19 — Architectural Shift to Operative Runtime

Yakoon has moved away from a classic Command/Controller framework toward an operative runtime with navigable semantic spaces.

## 2026-04-27 — Architecture Principles

- Kernel remains domain-neutral
- Domains emerge through composition
- Platform defines topology, not semantics
- Plugins own language

**Node as a term stays** — domains use domain language:
```
system = root.mount(System())
kitchen = world.add(Room("kitchen"))
```

## 2026-04-27 — Design Principle: Default Ports

The platform defines no command default ports. Commands stay pure. This is testability as a constructor contract. A command is only valid when its required capabilities are visible in the constructor. No silent `on_project` because "everyone needs it anyway."

## 2026-04-25 — Design Principle: Capabilities to the Point of Use

Capabilities are passed to the point of use. Good architecture minimizes debug interstices — no intermediate object without its own value.

## 2026-04-22 — Hierarchical Capability Composition Architecture

Each component defines what it can do (ports), not what it is — and is composed externally into larger units.

Pattern in one sentence: recursive, port-based system composition.

## 2026-04-22 — Ports e2c Migration

Data is passed. Behavior is injected.
- Session → passed in
- `engine.dispatch` → port
- `scheduler.*` → ports

## 2026-04-17 — Optimization as a Separate Step

Not just "we optimize later", but: optimization is a separate, systematic step — not a byproduct.

**Optimization tasks:**
1. Asset Delivery — ETag/304, Cache-Control
2. Large Files — Range Requests, streaming
3. Projection Pipeline — compile costs, resolver costs
4. Transport — WS message size, batching/diffing
5. Client Rendering — DOM updates, repaint cost
6. Caching — asset cache, projection cache

## 2026-04-14 — Formal Command Signature

The operation lives in the Command, not in transport. Therefore no GET/POST needed. Operation is modeled as a subcommand. Domain and operation are cleanly separated.

Signature: `<command> [operation] [args] [--params]`

## 2026-03-28 — View = Projection

A view is a projection. A projection is a deterministic, complete representation of the current UI state of a flow. It contains no behavior, no temporal logic, no sequencing. It is the result of rendering the current flow state. One file = one state.

## 2026-03-28 — Clean Separation: Flow, Effects, Domain Logic

The system strictly distinguishes three layers:

- **Flow (DSL / yield)** — describes temporal structure and interaction (`ask`, `show`, `delay`). Only here flows pause or continue.
- **Effects (side effects)** — technical actions like `Emit`, `AutoFocus`. Effects are not flow-controlling — pure side-effect execution.
- **Domain Logic (business)** — business processing like `validate`, `calculate_invoice`. Part of the Command, not part of the DSL or Engine responsibility.

**Important:**
- Only interaction with the outside world is modeled as DSL (`yield`)
- Domain logic must **not** be modeled as Step or Effect
- The Engine remains purely executing and knows no business rules

## 2026-03-22 — Flow-based Scheduler

The scheduler works flow-based instead of session-based. Scheduling via round-robin ensures fair CPU time. No flow dominates.

## 2026-03-22 — Yield in Commands

`DomainError` must NOT be used for validation — antipattern. Instead:
```python
if value < 3:
    yield step.reject(...)
    continue
```

## 2026-03-22 — Flow Types

- **NORMAL**: Step → AwaitInput → InputResolved → Next
- **VALIDATION**: Step → reject → AwaitInput
- **ERROR**: raise DomainError → Flow stop

## 2026-03-19 — Stateless Engine

The entire engine is now stateless:
- stateless engine
- stateful execution (generator)
- non-blocking runtime
- no semaphore, no tasks, no async-event

## 2026-03-16 — Host / Client Architecture

The platform has been rebuilt from a local CLI app to a real Host/Client runtime. Engine, Session, Runner, EventBus all run in the Host. Clients connect via transport and communicate exclusively through Events and InputEvents.

## 2026-03-16 — Runtime EventBus

Engine output no longer goes directly to a renderer, but through a Runtime EventBus. Sessions send events distributed to connected clients.

## 2026-03-16 — Interaction as Input Port

User interaction is modeled as its own port (`Interaction`). The Runner speaks exclusively to this interface, knows no UI. Interaction orchestrates input (prompt, forms) and converts to `InputEvent`.

## 2026-03-16 — Interaction Fully UI-agnostic

Interaction receives no UI objects — works with two callbacks: `read_input(prompt)` and `submit_input(event)`.

## 2026-03-16 — Base as Public API

Architecture strictly separates `base` from `platform`. Clients and plugins may only reference `base`, never `platform`. This keeps the runtime server-side while clients/plugins ship without access to internals.

## 2026-03-08 — Stream Presentation Pipeline

Presenter → render state → normalize/merge blocks → hand block sequence to DefaultInputService → play blocks sequentially → stream or emit passive blocks → on fields (prompt): wait via DialogService → accumulate PresentResult

Streamer → write exactly one block to the session.

## 2026-03-06 — Capabilities vs Business Logic

Plugins now provide only business modules and the shell. All other capabilities are modeled as Capabilities within Base and Platform.

## 2026-03-05 — EventStore

Event sourcing light with snapshots, index-on-write, cursor-based pagination, time-travel (`as_of`), and Memory/Postgres backends.

Entities addressed by 4 dimensions: `(domain, kind, space, entity_id)`

Tables:
- **Current Table** — materialized current state: `(entity_id, rev, data, updated_at)`
- **Revisions** — append-only change log: `(entity_id, rev, ts, patch, patch_format)`
- **Snapshots** — periodic materialization: `(entity_id, rev, ts, data)`

## 2026-02-27 — Streaming-First Model

Architecture switched from hybrid rendering (snapshot + streaming) to pure streaming-first. Container blocks (lists, key-value) are recursively and uniformly streamed.

## 2026-02-21 — Workflow as Plugin

WF commands (`wf.start`, `wf.input`, etc.) removed from Shell. Workflow is now a standalone module/plugin. The platform no longer knows Workflow as a core component. Engine accesses only via defined ports (`WorkflowInternal`, public contracts).

## 2026-02-21 — Platform Structure

Project structure separated into:
- `platform` → core (Engine, Directories, Services, Policies)
- `exts` → platform-extending modules (workflow, discovery)
- `apps` → business applications (crm, office)
- `posts` → infrastructure/host integration

## 2026-02-20 — Dispatch System Re-modeled

Union instead of inheritance. Two explicit transport types. No implicit payload semantics.

## 2026-02-14 — Policy System

Central `PolicyService`. Field type, validation, coercion defined via policies. Workflows and Presenter work only with policy references (e.g. `system:string`, `system:bool`).

## 2026-02-14 — Project-wide Formatting & Linting

Black (formatter) + Ruff (linter) introduced.

## 2026-02-10 — Workflow Never Exceeds User Privileges

Privilege escalation as a feature is not allowed. Workflows are orchestration, not permission shortcuts.

## 2026-02-06 — Desktop Technologies (Kivy)

Kivy chosen over Qt because: event-flow oriented (not form-centered), Python-first, MIT license, render-cycle control. Desktop = control over the machine.

## 2026-02-05 — DialogService & OutputAdapter

Global DialogManager dissolved. Session can route metadata to IO-Adapter. Service for Permissions & Roles introduced.

## 2026-02-04 — Permissions as Unix Rights

Permissions implemented as Unix rights (rx). Previous CommandSet concept dissolved — not scalable. Account supports roles and permissions loaded via `su`.

## 2025-05-29 — AI as Advisor (Intent Mapping Only)

AI acts exclusively as an advisor for intent mapping. It selects possible commands and domains — executes nothing. The platform remains the sole executing entity (actor). AI is purely advisory (consultant).

```python
intent = ai_chat_prompt("Teleport me to the knight's castle")
if intent.is_valid():
    if session.auto_confirm and intent.command.safe:
        engine.dispatch(intent.to_command_string())
    else:
        await ask(session, f"Execute: {intent.command.key} {intent.command.args}?")
```

## 2025-01-28 — Development Restart

After a long pause, development resumed with these decisions:
1. Web paused — focus on core platform
2. Split into 4 independent modules: `base`, `platform`, `hosts`, `compose`
3. Dependencies resolved via `compose`, not Engine
4. Services used for information exchange within the app
5. Services moved to Platform, Base accesses via Container (protocol files)
