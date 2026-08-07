# ADR 12: The Host is a Node — The Host Owns Execution

**Status:** Accepted — implemented on the experiment branch; production
migration follows

> **The runtime executes nodes. Some nodes happen to execute other nodes.**
>
> The node declares, the host interprets, the runtime coordinates. Today the
> runtime still treats hosts specially: it rewrites a node's `run` handler to
> delegate to a host, coupling the engine to host wiring. ADR-12 removes the
> host as an architecture type. A host is an ordinary node whose capabilities
> (execute / resolve) are ports; the runtime coordinates instead of
> interpreting; and the node that "is a host" keeps ownership of how it
> executes work.
>
> ADR-12 is not a new direction. It completes the line ADR-10 began: it
> removes the last runtime-owned behavior. ADR-10 shifted responsibility;
> ADR-12 removes the mechanical residue of the old responsibility. The runtime
> ends up knowing only nodes and ports — and the nodes that execute other
> nodes own that execution.

## Vocabulary

The ADR uses three terms that are worth fixing once:

> **Invocation** — a request to execute a node.
>
> **Context** — the immutable snapshot describing the conditions under
> which that invocation was started.
>
> **Node** — the executable unit consuming the Context.

**The canonical Invocation is normalized.** It is exactly two primary
fields:

```
node.path   → what is executed
args        → how it was invoked
```

Everything else is derived. The SDK's `Request` is a convenience view over
these two fields (`command` = `node.path`, tokens = `args`) — it re-parses
nothing and holds no truth. The shell's "token list with the command as
first token" (`["/cd", "/opt"]`) is deliberately gone: it duplicates
`node.path` and forces a reconstruction that the engine already knows.

The runtime executes nodes. Some nodes provide execution capabilities for
other nodes; the ADR calls those "hosts" only because the name is familiar —
they are not a separate type. A node that executes other nodes consumes the
same Context as every other node (Section 5) and owns its own execution
strategy (Section 6).

The resulting grammar of Yakoon is consistent:

```
Invocation  → describes the call
Context     → describes the call's data
Ports       → describe capabilities
Node        → consumes Context and Ports
Runtime     → coordinates
Host        → not a type; a node with the capability to execute other nodes
```

## Context

ADR-10 drew the ownership seam: the node declares reference expressions, the
host interprets them, the runtime coordinates. What remained was *mechanism* —
how the runtime actually hands a command to a host. Three pieces of special
treatment survive:

1. **Handler rewriting (`nodes/tree.py` `_make_host_handler`).** When a node
   declares `host: /boot/python/runtime`, the tree replaces that node's `run`
   handler with a delegating closure that finds the host node and calls
   `host_run(space)` — routing through the host, unchanged space.

2. **A bespoke coroutine stepper (`boot/python/runtime.py`).** The Python host
   is itself a node (`entry.run: pack:...runtime:run`). Its `run(space)` is an
   async generator the FlowCursor already drives — but *inside* it, a
   hand-written coroutine driver (`gen.send(None)` loop) executes the target's
   `main()`. The stepper is the host's execution strategy; what couples the
   engine is the handler rewriting (item 1), not the stepper.

3. **Bootstrap linking (`engine/bootstrap.py` `PackReference`).** The runtime
   imports host functions directly so the first host can start — a deliberate,
   narrow exception (ADR-10 "Bootstrap linking").

So today a "host" is a node, but a node with strings attached: ordinary nodes
point at it through a rewritten handler, and the engine wires hosts into the
tree by hand. The parked idea in `docs/roadmap/technical-debt.md` H named the
direction:

> A host is just a node with a job. If a host were an ordinary node
> (`async def main()` + SDK), the runtime would only say `await host.run()` and
> the host would use the same runtime services as any component. Its two
> capabilities (execute / resolve) would be offered via ports, not methods.

(The parked idea speaks of `main()`; the experiment showed the host's run
handler is an async generator — Contract B — so `run(space)` is the precise
shape. The direction is unchanged.)

## Problem

1. **The runtime rewrites handlers.** `_make_host_handler` reaches into the tree
   and swaps a node's `run` at build time. Rewriting hides where execution
   really happens and couples the engine to host wiring. The *host's own*
   stepper is not the problem — it is the host's execution strategy (Section 6).
   The problem is that the *engine* reaches into the tree to wire it.
2. **Host capabilities are methods, not ports.** `execute` and `resolve` are
   Python functions on the boot host module. Nothing else in the system can call
   a host's capabilities through the port mechanism — a component cannot, and a
   parallel host (.NET, a ticker host) must re-implement the same special
   treatment.
3. **The runtime still knows what a host is.** The word "host" appears in the
   engine (`_make_host_handler`, `host:` handling) and in the boot module. The
   ownership seam says the runtime should coordinate — not know host types.

## Decision

**Make the host an ordinary node.** The host node declares a run contract like
any component; its `run(space)` is an async generator the flow engine drives;
its two capabilities are offered as ports; the runtime coordinates and
interprets nothing; and the host keeps ownership of how it executes work.

### 1. A host is a node whose `run` is an async generator

The host node keeps `entry.run`. Its handler is an SDK-style async generator
that yields `Pulse`s through the flow engine — the same `FlowCursor` /
`CommandEngine` path every other node runs through. This is **already true
today**: `boot/python/runtime.py`'s `run(space)` is `async def` with `yield`
statements (Contract B), so the FlowCursor drives it directly.

The experiment (`tests/test_host_is_node.py` → now
`test_context_as_abi.py` + `test_host_context.py`)
proves the two contracts:

| Contract | What `main()` is | FlowCursor can drive it |
|----------|------------------|-------------------------|
| A | a coroutine hiding Pulses in `__await__()` (`io.write`) | no — Pulses swallowed |
| B | an async generator yielding Pulses directly | yes — unchanged |

The host is Contract B. The runtime needs no stepper of its own; it only
ever faces Pulse streams.

### 2. Capabilities become ports

The host's two capabilities are exposed as ports on the host node, following
the port convention (`ports.get("crm.contact.service")` — never bare names):

| Capability | Port | Meaning |
|------------|------|---------|
| execute | `host.execute` | run another node's `entry.run` through this host |
| resolve | `host.resolve` | interpret a node's `resources:` reference into a `Resource` (ADR-10) |

A command that declares `host:` reaches its host through the port
(`ports.get("host.execute")`), not through a rewritten `run` handler. The
runtime resolves the host node once — via the tree — and then coordinates; it
never knows what "execute" or "resolve" mean.

#### Why `execute` belongs to the host, not the runtime

`execute` is not a runtime service — it is host-owned. A host does not run
*a* node; it runs **its** nodes:

| Host | What `host.execute` means |
|------|---------------------------|
| PythonHost | load this Python pack, import it, run its `main()` |
| .NET host | start the CLR, load the assembly, call the entry point |
| Embedded host | flash the controller, start the process |
| Remote host | forward the reference, await the result elsewhere |

All offer the same contract (`host.execute`); each means something different.
If `execute` were a runtime service, the runtime would have to know *how* a
node is executed — precisely the knowledge Ownership First says it must not
hold. `host.execute` is the pendant to `crm.contact.service`: a capability a
specific node provides. A host is a provider like any other. It exports
capabilities through ports; those capabilities happen to belong to the runtime
domain.

This also removes the last unspoken assumption in the runtime: that
"execute" means "start Python." After ADR-12, `host.execute` does not read
"start Python" — it reads **"ask the responsible host to execute this
resource."** The host is the one that decides what executing means, and the
runtime is freed from even that knowledge.

### 3. The runtime coordinates, it does not interpret

The runtime keeps three jobs, all mechanical:

- **find** the host node for a given command (`host:` in yak.yml → tree lookup)
- **call** the host's `execute`/`resolve` port
- **drive** the resulting flow through `FlowCursor`/`CommandEngine` — the same
  scheduler, effects, and pipeline as any other flow

Nothing else. No scheme interpretation, no module import, no handler rewrite,
no host-type knowledge.

### 4. The Context is the invocation

> The Context describes the invocation — not the host, not the runtime, not
> the application. It is the frozen snapshot of *why this code is running*
> and *where*. Every node — command or host — reads it through the same SDK.

`context.current()` carries the immutable start conditions of an
invocation:

```
node.path       the node being invoked        (was: space.path)
args            the invocation arguments      (was: space.request.args())
flow.id         the executing flow            (was: space.flow_id)
session.key     reference to the live Session (was: space.session)
```

`session`, `cwd`, and `user` are **not** snapshotted — they are live state
owned by the SessionService (see "The Session is the one exception"). The
context carries only the session key; everything mutable is queried live
through the SDK.

**The invocation context is immutable and ephemeral.** It describes exactly
one invocation at one point in time. The context is not owned by the
scheduler, the host, or the application — it is derived when the invocation
is born, carried by the flow, and discarded when the flow ends.

### Invocation lifetime: the conditions of the start

**The invocation context answers one question only: under what conditions
was this invocation started?** It is the immutable snapshot established at
dispatch — like a process environment (`PWD=/tmp my_program`). A later
change in the parent's session is never expected to propagate into a
running child; neither does a session mutation propagate into a running
flow's context.

**The invocation context does not track subsequent mutations of the
session or runtime state. Components requiring current state must query the
owning service (e.g. session or filesystem) directly.**

This is why the context is deliberately immutable: it is *data about the
start*, not a live view of the world. When a flow needs current state, it
asks the owner of that state — `session.cwd()`, the filesystem, the
session service — never the context.

| Question | Source |
|----------|--------|
| Under what conditions was I started? | `context.current()` (snapshot) |
| What is the current cwd right now? | the filesystem / session service |
| Who am I (identity)? | `context.current()` — identity is a start condition |
| What changed mid-command? | the owning service, not the context |

Three possible models for what `context.current()` means:

| Model | Lifetime | Behavior after a session change |
|-------|----------|--------------------------------|
| A | **dispatch** | snapshot — `cwd` etc. frozen at dispatch, even if the flow later `chdir`s |
| B | **whole command** | dynamic within the flow — context reflects the current session state |
| C | **every step** | fully live — re-derived before every resume |

**Decision: Model A.** The invocation context is a **snapshot taken at
dispatch**. A flow that mutates its session (e.g. `cd` → `CwdEffect`) does
not see the change through `context.current()` in a later step of the
*same* flow; the next *command* is a new flow with a fresh snapshot.

Rationale:

- The context describes the **invocation** — *what was called and with
  what arguments* — not the mutable execution state. Arguments do not
  change mid-command; neither should the snapshot.
- This matches every execution boundary: a thread, process, or remote
  host receives the invocation snapshot once and never sees it change.
  Any other semantics would make the context's meaning host-dependent.
- Model C (per-step re-derivation) is the semantically live model, but it
  costs a re-derivation per step (measured ~65% of a step before the
  fix). Model A moves the cost to dispatch, where it is paid once — the
  optimization is a logical consequence of the semantics, not a shortcut.
- Model A keeps the flow self-contained: the flow carries its invocation,
  so it can migrate between schedulers/processes without re-deriving from
  a session the target may not have (ADR-12 Section 4).

Consequence: **a flow that needs to observe its own session mutation must
read the mutated state explicitly** (e.g. the `session` service or the
effect's result), not via `context.current()`. Today no pack reads
`context.current()` after mutating the session in the same flow, so the
snapshot is behaviorally safe — but the contract is now explicit.

### The Session is the one exception: a live reference, not a copy

The snapshot rule has exactly one exception — the **Session**. It is the
single piece of invocation data that other flows mutate (logout, `cd`,
`luma.current_box`, ...). Copying it into the snapshot would make it stale
by definition: a long-running flow that started at 08:00 must see a logout
at 09:00.

**The Session is live, shared state — like a database connection, not an
argument.** The invocation context therefore carries only the session
**key** (a reference), never a copy of the session's data. Components that
need the current session query the SessionService through the SDK
(`session.current()`), which is a live lookup — never the context.

```
Invocation (snapshot)              Live state (owned elsewhere)
├── node.path                      
├── args                            SessionService
├── flow.id                          ├── session (key, lang, data)
└── session.key ──────────────────→  └── cwd, user
```

Consequences:

- A logout, role change, or session timeout is visible **immediately** to a
  running flow — it reads live state, not a stale snapshot.
- Flow migration carries only the session key; every scheduler resolves the
  same session through the shared service.
- The SDK `session.current()` becomes a live (async) lookup over the Bus
  (port `session.current`), mirroring the existing `session.attach` /
  `detach` / `update` ports. `context.session()` as a snapshot is removed.
- `cwd` is session state (`cd` mutates it) and follows the session — read
  live, not from the snapshot.

**The Flow is the source of truth; the Context is its projection.** The
context is not persistent state — it is the most convenient representation
of the flow's invocation. The truth lives in the flow (its node, tokens,
and invocation snapshot); the context is derived from it once and carried.
This is why the context is never transported: you do not move a context,
you move the *flow* and its snapshot.

```
Flow ──derive──→ Context ──project──→ the host-friendly view
```

**The runtime derives the invocation context once, at dispatch.** The
derivation and the establishing are distinct responsibilities:
`derive_invocation_context(...)` produces the snapshot,
`establish_invocation_context(ctx)` makes it current for a step. The
direction is what matters: the flow is the source, the context is its
snapshot. This holds regardless of scheduler shape: round-robin, one task
per flow, multiple workers, parallel stepping, or several schedulers across
processes.

Because the context is represented as plain data (`dict`), it propagates
across any execution boundary without translation. **Execution boundaries
are responsible for propagating the invocation context** — the thread host
captures it and re-establishes it in the thread; the process host serializes
it and re-creates it in the child; the remote host forwards it. When a new
execution unit is created, whoever creates it carries the context over —
precisely the `ContextVar` philosophy. Not the scheduler guarantees the
right context; the creator of the boundary does. Serialization is a
consequence of this design, not its motivation.

A flow migrating between schedulers needs no context transfer: it carries
its node, tokens, and session reference, and the receiving scheduler calls
`derive_context(flow)` again. Scaling to multiple schedulers or processes is
a mechanical consequence, not an architecture problem.

**The runtime sets a raw invocation context through the Runtime API. The SDK
exposes that invocation as a typed `Context` model. The runtime never depends
on SDK types.**

This is ADR-11 applied to the invocation itself: the API defines the minimal
contract (a plain dict — the fields above, transported through the Runtime
API), the SDK provides the ergonomic surface (`context.current()`,
`context.node.path`, `context.request()`, typed `Session` / `Flow`). The
runtime produces data and transports it; it never models it — the SDK
interprets it. The host sits between them and — like any application —
speaks only the SDK.

The experiment proves the shape end-to-end (`test_context_as_abi.py`,
`test_host_context.py`): a parameterless `main()` reads its whole
world from `context.current()`, a host drives a real target command using
nothing but that context, and the target command sees the *same* context the
engine set. `NodeSpace` becomes an implementation detail of the engine — it
was only ever the engine's way of carrying these values to the host, which
immediately translated them back into the very same context.

### 5. Hosts consume the same Context as applications

Because the Context describes the invocation and not its interpreter, hosts
and commands share one contract. A host is not a special reader of special
data — it is a node whose `main()` does the same thing every command does:
`ctx = context.current(); drive(target_main())`.

| Before (host reads `space`) | After (host reads the same context) |
|-----------------------------|--------------------------------------|
| `space.path` → target | `ctx.node.path` → target |
| `space.session.get_data("fs:root")` → root | live `session.current()` → workspace |
| `space.session.cwd` → resolve | live `session.current()` → cwd |
| builds context for the target | passes the existing context through |
| `_build_context_dict` (translation) | gone — the engine derives the Context once, at dispatch |

This is the strongest form of "a host is a node": the host not only *runs
like* a node, it *reads like* one. It owns no special data and no special
API. Its one remaining difference is the execution strategy (Section 6) —
how it produces Pulses — and that is private.

### 6. The execution strategy belongs to the host

> The runtime does not know how work is executed. It only consumes a stream
> of `Pulse`s. The FlowCursor never executes anything — it only consumes
> Pulse streams.

Each host is responsible for driving its own execution model. The runtime
only sees a node producing a stream of `Pulse`s — the host's `main()` is an
async generator that yields those Pulses. *How* that node produces them is
entirely host-owned:

| Host | Execution strategy (the host's own) |
|------|-------------------------------------|
| `python/runtime` | drives Python coroutines through `__await__()` (today's stepper) |
| `python/thread` | drives Python coroutines inside a worker thread |
| `dotnet/process` | translates process communication into `Pulse`s |
| `remote` | translates network communication into `Pulse`s |
| `embedded` | flashes the controller, starts the process |

The `FlowCursor` therefore owns exactly one contract: **consume a stream of
`Pulse`s.** It never learns about Python coroutines, threads, processes, or
remote execution — those are host implementation details.

This is why the stepper must stay in the host, not move into the
`FlowCursor`: the FlowCursor runs in one process, on one event loop. A thread
or process host cannot use an engine-internal stepper — it needs its own
bridge. Moving the stepper into the engine would make thread/process/remote
hosts impossible (or force them to add special cases to the engine). With the
stepper in the host, each host owns how it executes — and the runtime remains
strategy-free.

The structure already declares this intent: `structure/python/thread/` and
`structure/dotnet/process/` exist as host nodes. What is missing is the
implementation — and ADR-12 makes those implementations possible without any
engine change.

The resulting hierarchy is strict: each level knows exactly one abstraction
of the level below it.

```
Runtime
    ↓
FlowCursor
        ↓
Pulse ABI
        ↓
Host
    ↓
Execution Strategy
        ↓
Application
```

### 7. Bootstrap linking shrinks to a first-start problem

`PackReference` survives only for the *first* host — the runtime must load
`boot/python/runtime:main` before any host can interpret references. That is a
one-time, mechanical link (ADR-10 already scopes it to host nodes only). Once
the first host runs, every later reference — including other hosts' — goes
through ports.

### 8. Parallel hosts, one mechanism

A ticker host, a .NET host, an embedded host — each is a node declaring
`host.execute` / `host.resolve` ports. The runtime does not enumerate host
kinds. A node's `host:` points at any node that offers these ports. This
generalizes ADR-10's "hosts run in parallel without conflicting" from resolve
to the full run contract.

## What disappears

| Today | After ADR-12 |
|-------|--------------|
| `_make_host_handler` (tree rewrites `run`) | gone — host reached via port |
| `host:` handled as a special tree case | `host:` resolves to a port lookup |
| Host capabilities as module functions (`run`/`resolve`) | ports `host.execute` / `host.resolve` |
| The unspoken assumption "execute = start Python" | "ask the responsible host to execute this resource" |
| The engine's knowledge of host wiring | gone — the engine coordinates via ports |
| `NodeSpace` as a hand-off object | an engine implementation detail — the Context is the invocation (Section 4) |
| `_build_context_dict` (host translates space → context) | gone — the engine derives the Context once, at dispatch |

## What stays

- `entry.run` — the run contract, unchanged.
- `resources:` / `resolve` semantics (ADR-10) — unchanged, now delivered via a port.
- `PackReference` bootstrap linking — but only for the first host.
- The boot host's *interpretation logic* (scheme parsing, module loading,
  `_shared.py` helpers) — stays behind the host's `main()`, unchanged.
- **The host's stepper** — stays in the PythonHost. It is the host's execution
  strategy (Section 6), not a runtime mechanism.

## Consequences

### Benefits

- **One execution path.** Every node — host or command — runs through the same
  flow engine. The engine no longer knows two host kinds; pulse routing and
  event send-back behave identically for every node.
- **The runtime knows no host type.** It coordinates; the port convention hides
  what a host is. This is Ownership First in its purest form.
- **Hosts compose.** A host can call another host via ports. Parallel hosts
  (ticker, .NET, embedded) share one mechanism, no engine changes.
- **New execution strategies without engine changes.** Thread, process, and
  remote hosts plug in as nodes — the stepper stays host-owned (Section 6).
- **Less engine surface.** `_make_host_handler` and its tree coupling vanish.
- **Testability.** Host behavior is testable like any command — through flows
  and ports, not through a bespoke driver.

### Trade-offs

- **One indirection hop.** Commands now resolve the host via a port lookup
  instead of a prebuilt closure. Cost is a dict lookup + call — negligible, but
  a real hop.
- **The engine must trust the host's Pulse stream.** The runtime can no longer
  special-case host behavior; it must accept whatever Pulses the host yields.
  For the PythonHost this is the status quo — it already yields through
  `run(space)`. For a future thread/process host it means the bridge must be
  correct by contract, not by inspection.

### Is the system simpler or more complex?

- **Engine: simpler.** The engine loses handler rewriting and the special host
  case. Its rule becomes uniform: *coordinate, don't interpret.*
- **Boot host: unchanged.** The host keeps its stepper and interpretation
  logic; only its wiring to the engine changes (ports instead of rewritten
  handlers).
- **System-wide: simpler.** One port convention replaces the special host
  wiring. The cost is concentrated in the port migration and its tests.
- **Abstraction, not lines.** The real gain is not deleting the stepper. Today
  the runtime *knows hosts* and *knows* `execute()`/`resolve()`. After ADR-12
  it *knows ports*. "Knows ports" is a strictly higher abstraction — one the
  runtime already applies to every business domain. The right metric is not
  "how many lines did we save" but "where does complexity disappear."
- **Risk, not size.** The design reduces code and special cases; the risk is
  behavioral (pulse/event plumbing) and migration, not structural growth.

## Open questions

1. **Port naming and lookup.** Should `host:` in yak.yml map to a well-known
   port (`host.execute`) or to an arbitrary named port the host declares? The
   former keeps yak.yml terse; the latter is more host-driven.
2. **`resolve` as a port vs a service.** ADR-10 proposes `runtime.resource`
   (a service that dispatches per node-host). A `host.resolve` port is the
   same delegation expressed as a port — which surface does the consumer see?
3. **Where does the tree store `host:`?** A node declaring `host:` still needs
   the runtime to find its host node. This is a tree lookup — does it live in
   the node's metadata (today) or in the Context once the engine resolves it?
   The experiment leaves metadata as the source; the Context carries what the
   invocation needs, not the wiring.
4. **First-host bootstrap scope.** Does `PackReference` survive only for the
   boot host, or for any node with no host of its own? ADR-10 says "host nodes
   with no host of their own" — ADR-12 should confirm the boundary.
5. **Stepper reuse across Python hosts.** The in-process `python/runtime`
   stepper and a future `python/thread` host share the coroutine-driving
   logic. Should that live in the boot package as a shared helper, or stay
   duplicated per host? (A shared helper inside `y5n-runtime-boot` is a
   host-owned library — not an engine concern.)
6. **`session.current()` surface.** The Session is live state (Section 4).
   The SDK needs a `session.current()` port over the Bus — how does it map
   to the existing `SessionService.get(key)`? And does `context.session()`
   become this live call, or is a separate `sdk.session.current()` the
   surface? This decides the migration of the ~15 packs that read
   `context.session().data` today.

## Implementation sketch (for later)

**Done on the experiment branch:** items 1–3 are implemented (Context ABI,
parameterless `main()`, engine derives once at dispatch). Remaining:

1. **Session as a live reference.** Add a `session.current` Bus port
   (SDK-facing, mirroring `session.attach`/`detach`/`update` in
   `SessionAdapter`) that resolves `SessionService.get(session_key)`. The
   SDK's `session.current()` calls it; `context.session()` no longer builds
   from a snapshot.
2. **Slim the invocation context.** `derive_invocation_context` keeps only
   `node.path`, `args`, `flow.id`, `session.key`. Drop `session` data,
   `user`, `workspace`, `cwd` — those become live lookups (session/cwd
   through the SessionService, `user` from the session).
3. **Migrate packs.** ~15 packs read `context.session().data` today
   (luma, ident) and `ctx.cwd` (cd, ls, pwd, man). Switch them to the live
   SDK surface (`session.current()`, `session.cwd()`).
4. Expose `host.execute` and `host.resolve` ports on the boot host node
   (per ADR-10's resolve service).
5. Narrow `PackReference` to the first host only.
6. Leave the PythonHost's stepper where it is — it is the host's execution
   strategy (Section 6), not an engine mechanism.
