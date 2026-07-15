# SDK — Command Capabilities

> **Draft.** This document describes a direction, not a specification.
> It captures an architectural idea that emerged while building
> the `python` executor and the `y5napi` context API.
> Nothing here is set in stone.

A Yakoon command is an independently executable program.
The Runtime does not define how a command is written —
it provides capabilities that a command may optionally use.

## Capability Levels

| Level | Capability | API | Available in |
|-------|-----------|-----|-------------|
| **0** | stdout | `print()` → stdout | every executor |
| **1** | Context | `context.current()` → request, session, path | `runtime`, `python` |
| **2** | UI SDK | `ui.table()`, `ui.form()` | `runtime`, `python` (future) |
| **3** | Services (RPC) | `services.*` → ports | `runtime`, `python` (future) |
| **4** | Runtime Effects | `yield Suspend()`, `yield StartTask()` | `runtime` |

### Level 0 — stdout

```python
print("Hello")
```

Every executor (`runtime`, `python`, `script`, `process`) can
translate stdout into Outcomes and send them to the client.
This is the universal ABI.

### Level 1 — Context

```python
from y5n.runtime.executor.napi import context

ctx = context.current()
print(ctx.request.arg(0))
print(ctx.session.get_data("theme"))
```

The executor places runtime information into the context before
starting the command. The command reads it. No async, no ports,
no scheduler — pure data.

### Level 2 — UI SDK (future)

```python
from y5n import ui

print(ui.table(columns=["Name", "Age"], rows=[["Alice", 42]]))
```

Structured output blocks (Table, Kv, Collapsible, Form, …)
are produced by the UI SDK and serialized to stdout.
The executor detects structured frames and translates them
into projection Outcomes. No runtime coupling.

### Level 3 — Services / RPC (future)

```python
from y5n import services

worlds = await services.worlds.list()
```

Port access through a JSON-RPC protocol on stdin/stdout.
The executor translates calls into runtime port invocations.
Available for `runtime` today, for `python` when the RPC
protocol is implemented.

### Level 4 — Runtime Effects

```python
yield Suspend()
yield StartTask(...)
```

Control the scheduler directly. These are the kernel operations
of the platform. Only available in the `runtime` executor.

## Architecture Rule

> **The Runtime does not define how a command is written.**
> **It provides capabilities that a command may optionally use.**

## Consequences

- A `print("Hello")` is a fully valid Yakoon command
- `yield` is not a mechanism for output, but for runtime control
- Forms, dialogs and patterns are UI libraries, not runtime concepts
- The executor translates the command's language into Outcomes for the scheduler
- Each capability level is discovered and built when a real command needs it
