# ADR 16: The Invocation Context Is Derived Once, at Dispatch

**Status:** Accepted — implemented (mechanism, not architecture)

> **The flow is the source of truth; the step projects it.**
>
> After the ADR-12 migration (host-is-a-node), engine-step throughput
> dropped by up to 37%. Per-step profiling showed the cost concentrated
> in re-deriving the invocation context: repeated Session attribute
> access on every step even when the session did not change. The fix
> derives the context **once, at dispatch**, stores it on the flow, and
> lets each step only re-establish it. Nothing is cached globally,
> nothing is stale — each flow owns its invocation snapshot.

## Context

ADR-12 moved the host from a special architecture type to an ordinary
node: `async def main()` + SDK, reading `context.current()` like any
command. The engine establishes the invocation context per step and
starts the node.

The migration was behaviorally correct but measurably slower. The engine
step re-derived the raw context dict from node + session + flow on every
step — even when the session had not changed. The cost was not the dict
construction or the `ContextVar.set` (both cheap); it was the repeated
attribute access on the session object.

## Problem

| Benchmark | dev (before) | after migration | Δ |
|-----------|-------------|-----------------|---|
| Flow-Switches | 512,206 ops/s | 324,197 ops/s | −37% |
| Session-Channel | 183,401 ops/s | 149,945 ops/s | −18% |
| Runtime-Mix | 52,748 ops/s | 40,629 ops/s | −23% |

Flow creation got faster (the migration improved it); step throughput got
slower. The loss was local and concentrated, not architectural.

Per-step profiling (`profile_step.py`) attributed the cost:

| Part | share of step |
|------|---------------|
| `set_invocation_context` (whole) | 65.8% |
| — repeated Session attribute access | ~52% |
| — dict construction | 11.4% |
| — `ContextVar.set` | 2.5% |

## Decision

Derive the invocation context **once, at dispatch**, and store it on the
flow. The step only re-establishes it:

```
dispatch:  flow.invocation = derive_invocation_context(node, session, flow_id, tokens)
step:      establish_invocation_context(flow.invocation)   # one ContextVar.set, ~97 ns
```

This is exactly the ADR-12 invariant restated: the flow is the source of
truth and carries its own context; the step projects it. The decision is
a mechanism change, not an architecture change.

## Consequences

### What was explicitly NOT done

- No global caching, no reuse of dicts across flows, no lazy context.
- No architecture rollback.
- The invariant "the context is freshly derived for the flow" stays — it
  now happens at dispatch, where the invocation is born.

### Result

| Benchmark | dev (before) | after fix | vs dev |
|-----------|-------------|-----------|--------|
| Flow-Switches | 512,206 | **982,792** | **+92%** |
| Session-Channel | 183,401 | **210,854** | **+15%** |
| Runtime-Mix | 52,748 | **57,725** | **+9%** |
| Massive 50k create | 41,744 | 41,596 | ~0% |
| Massive 100k create | 38,213 | 38,583 | ~0% |

Throughput is recovered and exceeds the pre-migration baseline. The
one-time derivation at dispatch is negligible for flow creation.

## How to reproduce

```
.venv/bin/python runtime/y5n-runtime-engine/tests/benchmarks/profile_step.py
.venv/bin/python -m pytest runtime/y5n-runtime-engine/tests/benchmarks/test_benchmarks.py -m benchmark -q -s
```
