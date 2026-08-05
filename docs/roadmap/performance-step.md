# Performance Investigation — Engine Step (ADR-12 migration)

**Date:** after the ADR-12 migration (host-is-node branch)
**Status:** measured, mechanism optimized

## The question

The engine-step throughput dropped after the ADR-12 migration:

| Benchmark | dev (before) | after | Δ |
|-----------|-------------|-------|---|
| Flow-Switches | 512,206 ops/s | 324,197 ops/s | −37% |
| Session-Channel | 183,401 ops/s | 149,945 ops/s | −18% |
| Runtime-Mix | 52,748 ops/s | 40,629 ops/s | −23% |
| Massive flows 10k create | 84,109 flows/s | 80,518 flows/s | −4% |
| Massive flows 50k create | 41,744 flows/s | 51,340 flows/s | +23% |
| Massive flows 100k create | 38,213 flows/s | 44,432 flows/s | +16% |
| Memory (Flow/AwaitEvent) | — | identical | 0% |

Flow creation got **faster**; throughput got **slower**. The loss is local.

## Diagnosis

Per-step profiling (`profile_step.py`) showed the cost concentrates inside
`set_invocation_context`:

| Part | share of step |
|------|---------------|
| `set_invocation_context` (whole) | 65.8% |
| — repeated Session attribute access | ~52% |
| — dict construction | 11.4% |
| — `ContextVar.set` | 2.5% |

The dict and ContextVar are cheap. The dominant cost was re-deriving the
session's attributes on every step even when the session did not change.

## Fix (mechanism, not architecture)

The invocation context is now derived **once, at dispatch**, and stored on
the flow (`flow.invocation`). The step only re-establishes it
(`establish_invocation_context(flow.invocation)` → one `ContextVar.set`,
~97 ns).

```
dispatch:  flow.invocation = derive_invocation_context(node, session, flow_id, tokens)
step:      establish_invocation_context(flow.invocation)   # ~97 ns
```

This is exactly the ADR-12 invariant restated: the flow is the source of
truth and carries its own context; the step projects it. Nothing is cached
globally, nothing is stale — each flow owns its invocation snapshot.

## Result (after fix)

| Benchmark | dev (before) | after fix | vs dev |
|-----------|-------------|-----------|--------|
| Flow-Switches | 512,206 | **982,792** | **+92%** |
| Session-Channel | 183,401 | **210,854** | **+15%** |
| Runtime-Mix | 52,748 | **57,725** | **+9%** |
| Massive 50k create | 41,744 | 41,596 | ~0% |
| Massive 100k create | 38,213 | 38,583 | ~0% |

The throughput is recovered and exceeds the pre-migration baseline. The
one-time derivation at dispatch is negligible for flow creation.

## What was explicitly NOT done

- No global caching, no reuse of dicts across flows, no lazy context.
- No architecture rollback.
- The invariant "the context is freshly derived for the flow" stays; it
  now happens at dispatch, where the invocation is born.

## How to reproduce

```
.venv/bin/python runtime/y5n-runtime-engine/tests/benchmarks/profile_step.py
.venv/bin/python -m pytest runtime/y5n-runtime-engine/tests/benchmarks/test_benchmarks.py -m benchmark -q -s
```
