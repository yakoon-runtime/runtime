# ADR 14: The Runtime Is the Smallest Scalable Unit

**Status:** Closed

```
Result:
Not adopted for production.

Reason:
The experiment proved the architecture technically viable, but showed no
measurable benefit for Yakoon's real workload. The production architecture
remains: one runtime = one scheduler. Horizontal scaling is achieved by
running multiple runtime instances behind a load balancer.
```

The ProcessPool and the SchedulerPool remain experiment code on the
`experiment/distributed-runtime` branch. The branch is closed and deleted;
the decision and its measurements live on in this ADR.

> **The runtime is the smallest replicable unit. The scheduler is not the
> bottleneck of the runtime. More schedulers solve the wrong problem.**
>
> A runtime owns a replicated read-only tree, a stateless engine, a session
> store, and a set of schedulers. Because almost no component holds exclusive
> state, a runtime can be started, stopped, and replicated as a whole —
> without any internal distribution machinery. Scaling Yakoon is an
> operational decision (start more runtimes), not a runtime decision (build
> a process pool inside one runtime).
>
> This ADR records the experiment that reached this decision, the numbers it
> produced, and the questions it left open. The experiment is kept as a
> research branch; the ProcessPool is deliberately **not** adopted into the
> product architecture.

## The question

The experiment began with a single founding question:

> **What is the smallest unit that unambiguously belongs to an owner?**

Its engineering form was:

> Can the engine and scheduler (or the whole runtime) run as multiple workers
> behind an internal router — like NGINX, but for invocations?

## What the experiment built

In five steps, on `experiment/distributed-runtime`:

1. **Experiment sketch** — ownership, not load balancing. The router should
   need no scheduler knowledge; it only maps `session → worker`.
2. **SchedulerPool** — a runtime owns a set of schedulers over one tree. The
   pool answers exactly one question: *who owns this session?* Ownership is
   deterministic `crc32(session.key)`, never Python's process-randomized
   `hash()`.
3. **Runtime settings own the pool** — `scheduler_count` is configuration,
   not architecture.
4. **RuntimeWorker spike** — the engine and scheduler as a standalone child
   process, serving newline-delimited JSON over stdio. Proved: engine runs in
   a child, scheduler completes flows there, completions arrive as events,
   IPC is ~0.013 ms per JSON ping, start/stop is clean.
5. **ProcessPool** — real subprocesses, one per worker. `owner(session)`
   routes to the owning process; `dispatch()` sends the invocation and awaits
   `flow_complete`.

## The measurements

Two load shapes were measured.

### Pulse-based flows (I/O-like, GIL-releasing)

`yield Pulse()` releases the GIL — this is the shape of most real flows,
which mostly wait on events.

| Measurement | Result |
|---|---|
| Step (scheduler + engine) | **~960,000 steps/s** |
| Complete flows, 1 scheduler | **~40–50,000 flows/s** |
| Complete flows, 3 in-process schedulers | **0.76x** (slower) |
| Complete flows, 3 real processes, parallel dispatch | **0.56x** (slower) |

### CPU-bound flows (no awaits in the hot loop)

| Measurement | Result |
|---|---|
| 3 × 5M arithmetic, 1 scheduler (GIL serializes) | 0.63s |

## The finding: the scheduler is not the bottleneck

The numbers contradict the initial hypothesis *"more schedulers make Yakoon
faster"*. Even with **correct parallel dispatch** (one session per worker,
all dispatched at once), the process pool is slower for pulse-heavy flows —
because a single in-process scheduler already cooperates perfectly when the
GIL is released.

The runtime does not spend its time scheduling. It spends it on:

- dispatch
- resolver
- invocation construction
- Python object allocation

> **More schedulers solve the wrong problem.** The scheduler was never the
> scaling constraint. The constraint — if it is ever reached — lies in the
> dispatch path, not in the scheduler.

For Yakoon's real workload this is a non-issue: a flow is a user command, and
even a large installation with 10,000 concurrent users produces a few hundred
commands per second. ~50,000 flows/s is ~100x above the realistic need.

## What the experiment answered

| Question | Answer |
|---|---|
| Can a runtime be replicated? | **Yes** — the tree is replicated read-only, the engine is stateless |
| Can a worker run autonomously? | **Yes** — own engine + scheduler, built in-process |
| Does session ownership work? | **Yes** — deterministic crc32, stable across restarts |
| Does IPC work? | **Yes** — ~0.013 ms per JSON ping over stdio |
| Is the scheduler the scaling bottleneck? | **No** |

## Adopted knowledge

Even though the experiment is not adopted as a whole, its findings remain
valid and valuable:

- ✅ The runtime is replicable.
- ✅ The engine is replicable (stateless).
- ✅ The scheduler is replicable.
- ✅ Session ownership works (deterministic crc32).
- ✅ JSON/stdio works as a worker protocol (~0.013 ms per ping).
- ✅ Workers build their own engine — the parent never injects code.
- ✅ IPC is practically a non-issue.

## Not adopted

- ❌ ProcessPool inside one runtime.
- ❌ Multiple schedulers to increase throughput.
- ❌ WorkerPool as product architecture.

**Reason:** the typical Yakoon workload is predominantly event- and
wait-based. The additional complexity brings no measurable benefit on a
single machine.

## What the experiment did NOT show

The ProcessPool proved that workers are autonomous and ownership works — the
preconditions for running multiple runtimes. It did not prove that a runtime
needs internal process management. On the contrary: because almost no
component holds exclusive state, the simpler architecture holds:

```
Client
      │
      ▼
LoadBalancer
      │
 ┌────┴────┐
 ▼         ▼
Runtime   Runtime
```

This is simpler than a runtime that internally owns a process pool. It also
keeps the runtime fully deployment-agnostic: whether one runtime, ten behind
a load balancer, or a hundred across machines — that is an **operational
decision**, not a runtime decision.

## Decision

1. **The runtime is the smallest scalable unit.** Scaling is operational:
   start more runtimes. No internal process pool is built into the product.
2. **The experiment is not adopted into production.** Neither the ProcessPool
   nor the SchedulerPool ships in the product. `build_machine` continues to
   use a single scheduler; `scheduler_count` is not part of the production
   settings.
3. **The branch is closed and deleted.** The code remains reachable in git
   history; the decision and the measurements live on in this ADR.

## Capacity estimate: the runtime is never the bottleneck

The measurements allow a different question than "how fast is Yakoon?":

> **How large must a customer be before Yakoon reaches its limits?**

Typical mid-sized company (250 employees, 120 regular users, 30 concurrently
active, ~2 commands/s each):

```
30 × 2 = 60 flows/s  →  60 / 50,000 = 0.12% of capacity
```

Large installation (10,000 employees, 2,000 concurrently active, ~0.5
commands/s each):

```
2,000 × 0.5 = 1,000 flows/s  →  1,000 / 50,000 = 2% of capacity
```

The runtime is effectively idle. And these numbers measure only the runtime
itself — not PostgreSQL, REST calls, ERP, the filesystem, the network, LLMs,
or document projection. In a real command (`contact list`), the runtime may
take 20 µs while PostgreSQL takes 18 ms, Jinja 5 ms, the compiler 2 ms — the
user experiences 25 ms, of which under 0.1% comes from the runtime.

**Consequence:** architecture no longer has to be traded against performance.
If a more elegant solution were 2% slower, it should still be chosen — the
runtime works at fractions of a percent of the capacity a real installation
needs. Properties like clarity, determinism, maintainability, and
extensibility outweigh squeezing out a few more thousand flows per second.

## Open questions

The experiment redirected optimization attention away from the scheduler
toward the dispatch path. These remain open research questions — they are
**not** production goals:

- How expensive is the resolver?
- How expensive is invocation/context construction?
- How expensive is dispatch?
- How expensive are projections?
- Where do most Python allocations happen?

If throughput ever becomes a goal, these — not the scheduler — are the
profiling targets.

## Why this is an improvement

Most experiments in Yakoon's history have first **disproved** an assumption:

- Host as node
- Error as invocation
- Invocation instead of request
- SchedulerPool
- ProcessPool

And every time the system became **simpler**. This experiment did not show
that Yakoon gets faster with processes. It showed that the complexity is not
needed to reach the scaling goals. That is the same pattern: the value of the
experiment is the size of the architecture it made unnecessary.
