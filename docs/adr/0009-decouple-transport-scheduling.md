# ADR 9: Decouple Transport and Scheduling — Effect as Runtime Protocol

**Status:** Draft for discussion

## Context

In the current architecture, `yield` carries multiple concerns simultaneously:

1. **Suspend** the flow (generator protocol)
2. **Transport** a Marker from SDK to the runtime
3. **Describe** an effect implicitly through the Marker kind

Every SDK call follows this pattern:

```python
def __await__(self):
    yield Marker(MarkerKind.WRITE, value)
```

The consumer chain then translates: `Marker → drive() → Outcome → Effect`. This layered
translation exists because `Marker` is an SDK-internal protocol that must cross the
coroutine boundary into the engine's effect system.

## Problem

The coupling of transport and scheduling has four consequences:

- **`yield` is overloaded.** A single language construct expresses suspension,
  transport, and effect description simultaneously.
- **`drive()` exists as a translator.** 182 lines bridge the Marker protocol to the
  engine's Outcome/Effect types. Every new Marker kind needs a handler in `drive()`.
- **Two parallel type systems.** Marker (13 kinds) and Effect (7 types) overlap in
  semantics but are separate hierarchies.
- **The boot layer is an async-generator middleman.** `boot/python/runtime.py` is
  wired between `drive()` and `FlowCursor` solely to connect these protocols.

## Three Models

### Model A — Current

```
SDK: yield Marker(MarkerKind.WRITE, value)
  → drive() (Marker → Outcome)
  → Boot run() (async gen middleman)
  → FlowCursor.next()
  → CommandEngine.step_flow()
  → Scheduler
```

Marker is simultaneously transport format, effect description, and suspend signal.

### Model B — Queue (ADR draft)

```
SDK: flow.effect_queue.append(WriteEffect(...)); yield CONTROL
  → FlowCursor.next()
  → Scheduler (drain queue + apply effects + handle control)
```

Queue separates transport from scheduling, but introduces owned state (who empties
it? when? can it hold multiple effects? who owns it?). For the common case of
"one effect per yield", the queue adds complexity without benefit.

### Model C — Effect as yield value (proposed)

```
SDK: yield WriteEffect(...)
  → FlowCursor.next()
  → Scheduler (isinstance(value, Effect) → apply + step)
```

No queue. No Marker. No `drive()`. The yield value *is* the Effect. The scheduler
inspects the yielded value directly.

## Decision

Adopt **Model C**.

### Principle

> **Effect becomes the runtime protocol.** What the SDK yields is what the runtime
> applies. No translation layer.

### What `yield` means

From the SDK's perspective:

```python
yield WriteEffect(view, mode="replace")
```

means:

> "Here is an effect. Process it, then continue me."

From the scheduler's perspective, after `step(flow)`:

```python
value = step(flow)
if isinstance(value, Effect):
    apply(value, flow, session)
```

`yield` retains a dual role (transport + suspend), but the transport is now
semantically uniform: it carries an Effect. No secondary protocol (Marker), no
translation chain.

### What disappears

| Component | Lines | Reason |
|-----------|-------|--------|
| `drive()` | 182 | No Marker→Outcome translation needed |
| `Marker` / `MarkerKind` | 55 | Replaced by direct Effect types |
| `host/handlers.py` | 46 | No Marker handlers needed |
| Boot async-generator middleman | ~40 | Boot becomes a direct step() caller |
| `Outcome` effects field | ~10 | Effects travel via yield, not Outcome |
| SDK `__await__` boilerplate | varies | No Marker wrapping needed |

### What stays

| Component | Why |
|-----------|-----|
| **Generator** | Flow execution state — irreplaceable |
| **Scheduler** | Deterministic flow lifecycle |
| **FlowCursor** | Generator stepping — unchanged |
| **Effect types** | Move from engine-internal to SDK-facing |
| **Control types** | Flow lifecycle — unchanged |

### Effect types become the SDK contract

Today, Effect types (`EmitView`, `StartTask`, etc.) are engine-internal. In Model C,
they become the public contract between SDK and runtime. The SDK produces Effects
directly; the runtime applies them.

## Interactive patterns (`PROMPT`, `RECEIVE`, `SEND`)

These require bidirectional communication — the SDK yields an effect and expects a
response value back. In Model C, two approaches exist:

### Option 1: `yield` with response channel

```python
class ReceiveEffect(Effect):
    channel: str
    scope: Scope
    response: asyncio.Future = field(default_factory=asyncio.Future)

async def receive():
    effect = ReceiveEffect(channel="input", scope=Scope.FLOW)
    yield effect
    return await effect.response  # scheduler resolves this future
```

The scheduler sets `effect.response.set_result(value)` when an event arrives.

### Option 2: Scheduler injects response via generator.send()

```python
class ReceiveEffect(Effect):
    channel: str
    scope: Scope

async def receive():
    value = yield ReceiveEffect(channel="input", scope=Scope.FLOW)
    return value
```

The scheduler calls `flow.cursor.send(value)` to deliver the response. This
preserves the existing `send()` mechanism from the generator protocol.

Both work without Marker. Option 2 is simpler and matches the current `drive()`
pattern for `PROMPT`/`RECEIVE`/`SEND`.

## Consequences

### Benefits

- **One type system.** Effect is both the SDK output and the engine input.
- **`yield` has one type.** Always an Effect (or a Control value for lifecycle).
- **`drive()` disappears.** ~180 lines of translation vanish.
- **New features are simpler.** A new capability = a new Effect type + a handler.
- **The boot layer simplifies.** No async-generator middleman.
- **No owned state.** Unlike a queue, the yield protocol needs no storage.

### Trade-offs

- **Existing Marker-based SDK code needs migration.** All SDK modules change their
  `__await__` implementation.
- **Scheduler must inspect yield values.** Simple `isinstance` check, but new
  concern for the scheduler.
- **Interactive patterns need a response mechanism.** Option 2 (generator.send())
  is natural but must be explicitly designed.

### Open questions

1. Should every Effect be a `@dataclass(frozen=True)` like today, or are mutable
   fields (like `response: Future`) acceptable for interactive patterns?

2. How does the scheduler distinguish an Effect from a Control value? Both are
   yielded. Option: `isinstance(value, Effect)` vs `isinstance(value, Control)`,
   or a single type with a discriminant.

3. Should the engine-internal Effect hierarchy be the same as the SDK-facing
   Effect hierarchy, or should there be a separate SDK Effect set that maps onto
   engine Effects?

4. Can Outcome be reduced to just `.control` if effects are no longer part of it?
