# ADR 9: Decouple Transport and Scheduling — Pulse as the Flow's Yield

**Status:** Accepted (implemented on `effect-queue`)

> **A Flow executes until it emits its next Pulse.**

A Pulse is what a Flow hands to the runtime at every yield point. It carries
the Flow's intent (`effects`) and its lifecycle instruction (`control`). The
runtime applies the Pulse and decides when the Flow runs again. The Flow does
not ask, request, or message — it pulses: it runs, reaches a decision point,
hands over control, waits, and lives on.

## Context

Before this ADR, `yield` carried multiple concerns simultaneously:

1. **Suspend** the flow (generator protocol)
2. **Transport** a Marker from SDK to the runtime
3. **Describe** an effect implicitly through the Marker kind

Every SDK call followed this pattern:

```python
def __await__(self):
    yield Marker(MarkerKind.WRITE, value)
```

The consumer chain then translated: `Marker → drive() → Pulse → Effect`. This layered
translation existed because `Marker` was an SDK-internal protocol that had to cross the
coroutine boundary into the engine's effect system.

## Problem

The coupling of transport and scheduling had four consequences:

- **`yield` was overloaded.** A single language construct expressed suspension,
  transport, and effect description simultaneously.
- **`drive()` existed as a translator.** 182 lines bridged the Marker protocol to the
  engine's Pulse/Effect types. Every new Marker kind needed a handler in `drive()`.
- **Two parallel type systems.** Marker (13 kinds) and Effect (7 types) overlapped in
  semantics but were separate hierarchies.
- **The boot layer was an async-generator middleman.** `boot/python/runtime.py` was
  wired between `drive()` and `FlowCursor` solely to connect these protocols.

## Three Models

### Model A — Before

```
SDK: yield Marker(MarkerKind.WRITE, value)
  → drive() (Marker → Pulse)
  → Boot run() (async gen middleman)
  → FlowCursor.next()
  → CommandEngine.step_flow()
  → Scheduler
```

Marker was simultaneously transport format, effect description, and suspend signal.

### Model B — Queue (rejected)

```
SDK: flow.effect_queue.append(WriteEffect(...)); yield CONTROL
  → FlowCursor.next()
  → Scheduler (drain queue + apply effects + handle control)
```

A queue separates transport from scheduling, but introduces owned state (who empties
it? when? can it hold multiple effects? who owns it?). For the common case of
"one effect per yield", the queue adds complexity without benefit. Rejected.

### Model C — Pulse as yield value (adopted)

```
SDK: yield Pulse(effects=[EmitView(...)], control=...)
  → FlowCursor.next()
  → CommandEngine.step_flow()
  → Scheduler (apply effects + handle control)
```

No queue. No Marker. No `drive()`. The yield value is a `Pulse` — a named structure
carrying `effects` and `control`. The scheduler applies effects directly and decides
the flow's next state from the control.

## Decision

Adopt **Model C**. Implemented in commit `d5fcec86`.

### Principle

> **A Flow executes until it emits its next Pulse.**

The Pulse is the unit of interaction between a Flow and the runtime. `step_flow()`
means "let the flow run until its next Pulse." The scheduler applies the Pulse's
effects and determines, via control, what happens next.

### What `yield` means

From the SDK's perspective:

```python
yield Pulse(effects=[EmitView(view, mode="replace")])
```

means:

> "Here is my intent. Apply it, then continue me."

From the scheduler's perspective, after `step_flow(flow)`:

```python
pulse = await step_flow(flow, session)
if pulse and pulse.effects:
    await apply(pulse.effects, flow, session)
if pulse and pulse.control:
    handle(pulse.control, flow, session)
```

`yield` retains a dual role (transport + suspend), but the transport is now
semantically uniform: it carries a Pulse. No secondary protocol (Marker), no
translation chain.

### What disappeared

| Component | Lines | Reason |
|-----------|-------|--------|
| `drive()` | 182 | No Marker→Pulse translation needed |
| `Marker` / `MarkerKind` | 55 | Replaced by direct Effect types |
| `host/handlers.py` | 46 | No Marker handlers needed |
| Boot async-generator middleman | ~40 | Boot steps the coroutine directly |
| SDK `__await__` Marker wrapping | varies | No Marker wrapping needed |

### What stays

| Component | Why |
|-----------|-----|
| **Generator** | Flow execution state — irreplaceable |
| **Scheduler** | Deterministic flow lifecycle |
| **FlowCursor** | Generator stepping — unchanged |
| **Effect types** | Now SDK-facing contract |
| **Control types** | Flow lifecycle — unchanged |

### Effect types become the SDK contract

Effect types (`EmitView`, `StartTask`, `CwdEffect`, etc.) moved from engine-internal
to SDK-facing. The SDK produces Effects inside a Pulse; the runtime applies them.

## Boot-level effects

Some Effects are handled by the boot, not the engine:

| Effect | Boot behavior |
|--------|---------------|
| `CwdEffect` | `session.set_cwd(path)` |
| `FlowStopEffect` | stop the target flow |
| `FlowFgEffect` | set the foreground flow |
| `FlowListEffect` | return the flow list (response) |
| `FlowBgEffect` | clear the foreground flow (response) |

The boot intercepts these in its coroutine stepper, executes them, and continues
without yielding a Pulse upstream.

## Interactive patterns (`PROMPT`, `RECEIVE`, `SEND`)

These require bidirectional communication — the SDK yields a Pulse and expects a
response value back. Adopted approach: the generator `send()` mechanism.

```python
class _Prompt:
    def __await__(self):
        result = yield Pulse(
            effects=[Foreground(), EmitView(view, persist=True)],
            control=AwaitEvent("__user__", scope=Scope.USER_INPUT),
        )
        return result
```

The runtime yields the Pulse upstream, receives the input event, and delivers it via
`gen.send(event)`. This preserves the existing generator protocol — no futures in
Effects, no response channels.

## Consequences

### Benefits

- **One type system.** Effect is both the SDK output and the engine input.
- **`yield` has one type.** A Pulse carrying effects and control.
- **`drive()` disappears.** ~180 lines of translation vanish.
- **New features are simpler.** A new capability = a new Effect type + a handler.
- **The boot layer simplifies.** Direct coroutine stepping, no middleman.
- **No owned state.** Unlike a queue, the yield protocol needs no storage.

### Trade-offs

- **SDK modules changed.** All `__await__` implementations now build Pulses.
- **Boot inspects yield values.** Simple `isinstance` checks for boot-level Effects.
- **`first`-write mode tracking** moved into the boot's stepper (replace → append).

### Open questions

1. Should every Effect be a `@dataclass(frozen=True)` like today, or are mutable
   fields (like `response: Future`) acceptable for interactive patterns?

2. Can the boot-level Effects (`CwdEffect`, `FlowListEffect`, ...) eventually move
   into the engine's EffectExecutor, so the boot needs no special-casing?

3. `Pulse.value` is currently unused by the runtime. Should it stay or go?
