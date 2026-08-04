# ADR 12: The Host is a Node — The Host Owns Execution

**Status:** Draft — design exploration, no code changes yet

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
> **Context** — the immutable snapshot describing that invocation.
>
> **Node** — the executable unit consuming the Context.

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

The experiment (`tests/test_experiment_host_is_node.py` → now
`test_experiment_context_as_abi.py` + `test_experiment_host_context.py`)
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

`context.current()` is the single data source. It carries exactly what an
invocation is:

```
node.path    the node being invoked        (was: space.path)
workspace    the workspace root            (was: space.session "fs:root")
cwd          the working directory         (was: space.session.cwd)
session      key, lang, interaction, data  (was: space.session)
user         identity of the caller        (was: session identity)
flow         id of the executing flow      (was: space.flow_id)
tokens       the invocation arguments      (was: space.request.args())
```

`context.current()` is read-only, frozen, and set exactly once — by the
engine, before the flow starts. The host does **not** build it; the host
reads it, like any application.

The experiment proves the shape end-to-end (`test_experiment_context_as_abi.py`,
`test_experiment_host_context.py`): a parameterless `main()` reads its whole
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
| `space.session.get_data("fs:root")` → root | `ctx.workspace` → root |
| `space.session.cwd` → resolve | `ctx.cwd` → resolve |
| builds context for the target | passes the existing context through |
| `_build_context_dict` (translation) | gone — one context, set once |

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
| `_build_context_dict` (host translates space → context) | gone — the engine sets the Context once |

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

## Implementation sketch (for later)

1. **Set the Context where NodeSpace is built.** In `engine.py` and
   `tree.py` (SETUP), replace `NodeSpace(...)` with building the SDK Context
   (`node.path`, `workspace`, `cwd`, `session`, `user`, `flow`, `tokens`)
   and setting it via the SDK contextvar — the ABI (Section 4).
2. **Migrate the boot host.** `boot/python/runtime.py`: read `ctx.node.path`,
   `ctx.workspace`, `ctx.cwd` instead of `space.*`; delete
   `_build_context_dict`; keep the stepper (Section 6). The flow engine keeps
   driving the host's `main()` async generator.
3. **Migrate engine consumers.** `interactor.py` and `projector.py` read
   `session.lang` / the target path from the Context instead of `space`.
4. Expose `host.execute` and `host.resolve` ports on the boot host node
   (per ADR-10's resolve service).
5. Remove `_make_host_handler`; a node with `host:` resolves its host via a
   port lookup.
6. Narrow `PackReference` to the first host only.
7. Migrate tests: `test_resources.py` host calls → port-based; add a flow-level
   test that a `host:`-declared command runs end-to-end through
   `FlowCursor`/`CommandEngine` (already sketched in the experiment files).
8. Leave the PythonHost's stepper where it is — it is the host's execution
   strategy (Section 6), not an engine mechanism.
