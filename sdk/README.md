# SDK — Command Capabilities

The Python SDK is the first-class interface for writing Yakoon commands.

```python
from y5n.sdk import context, fs, io, models, ports, scheduler, session, viewport
```

## Modules

| Module | Import | Purpose |
|--------|--------|---------|
| `context` | `from y5n.sdk import context` | Read-only snapshot of the current invocation |
| `io` | `from y5n.sdk import io` | Text / structured output and error messages |
| `timer` | `from y5n.sdk import timer` | Delay and scheduling helpers |
| `scheduler` | `from y5n.sdk import scheduler` | Process / flow management (list, stop, fg, bg) |
| `network` | `from y5n.sdk import network` | Remote runtime discovery and connection |
| `viewport` | `from y5n.sdk import viewport` | Client viewport commands (clear, connect) |
| `session` | `from y5n.sdk import session` | Session management (list, attach, detach) |
| `fs` | `from y5n.sdk import fs` | Filesystem operations (chdir) |
| `models` | `from y5n.sdk.models import Document, ...` | Typed YDS document builder (generated from `sdk/spec/yds/yds-v1.yaml`) |
| `ports` | `from y5n.sdk import ports` | Service / port access (provide + consume) |

A backward-compatible `runtime` facade is available for code that prefers a single
entry point:

```python
from y5n.sdk import io, timer

await io.write("hello")
await timer.delay(2)
```

## Context — Read the World

```python
from y5n.sdk import context

req = context.request()       # parsed invocation arguments
ctx = context.current()       # cwd, workspace, user, session
sess = context.session()      # session-scoped data
```

## IO — Text & Structured Output

```python
from y5n.sdk import io

await io.write("hello")                    # plain text output
await io.write({"key": "structured"})      # dict output
await io.write(doc)                        # YdsModel → auto to_dict()
await io.write(Document(...))              # YDS document

await io.error("something went wrong")
```

## Timer — Delays

```python
from y5n.sdk import timer

await timer.delay(2.5)                     # sleep seconds
await timer.delay_until(1234567890.0)      # sleep until timestamp
```

## Scheduler — Flow Management

```python
from y5n.sdk import scheduler

flows = await scheduler.flows()
await scheduler.stop(flow_id)
await scheduler.foreground(flow_id)
await scheduler.background()
```

## Network — Remote Runtimes

```python
from y5n.sdk import network

runtimes = await network.list()
url = await network.resolve(name)
```

## Viewport — Client Viewport Commands

```python
from y5n.sdk import viewport

await viewport.clear()
await viewport.connect(url=url, name=name)
```

## Session — Session Management

```python
from y5n.sdk import session

rows = await session.list()
await session.attach("other-key")
await session.detach()
```

The current session key is available from context:

```python
from y5n.sdk import context

key = context.session().key
```

## Filesystem — Working Directory

```python
from y5n.sdk import fs

await fs.chdir("/tmp")
```

The current working directory can be read from context:

```python
from y5n.sdk import context

path = context.session().cwd
```

## Models — Typed YDS Documents

Generated from `spec/yds/yds-v1.yaml` via `sdk/y5n-sdk-python/generate.sh`.

```python
from y5n.sdk.models import Document, Header, Paragraph, InlineText

doc = Document(
    header=Header(title="Hello"),
    blocks=[
        Paragraph(text=[InlineText(text="World")]),
    ],
)
await io.write(doc)   # auto-converts via .to_dict()
```

Every model class is a `@dataclass(slots=True, kw_only=True)` that inherits from
`YdsModel` and provides `.to_dict()`. Fields with `None` values are omitted from
the serialized output. The `type` discriminator is set automatically for block and
inline types.

### Generated classes

| Category | Classes |
|----------|---------|
| **Root** | `Document` |
| **Header** | `Header` |
| **Block (base)** | `Block` (subclass for container type hints) |
| **Blocks** | `Text`, `Paragraph`, `Heading`, `Pre`, `Rule`, `Spacer`, `List`, `ListItem`, `Kv`, `KvItem`, `Table`, `Fields`, `Actions`, `Section`, `Stack`, `Flow`, `Collapsible`, `Image` |
| **Inline (base)** | `Inline` (subclass for container type hints) |
| **Inlines** | `InlineText`, `InlineStrong`, `InlineEm`, `InlineUnderline`, `InlineCode`, `InlineLink`, `InlineCmd`, `InlineArg`, `InlineMark`, `InlineSelect`, `InlineSpace`, `InlineBreak` |
| **Standalone** | `TableColumn`, `Field`, `Action` |

## Architecture

```text
Command                       Runtime
  │                            │
  ├─ context.current() ────────┤  (data snapshot, no call)
  │                            │
  ├─ await io.write(doc) ─────┤
  │                           │
  │  YdsModel.to_dict() ──────┤  (SDK serializes to plain dict)
  │                           │
  │  Pulse(effects=[...]) ────┤  (yielded via __await__)
  │                           │
  └─ [done] ── StopIteration ──┘
```

The runtime drives the command coroutine via `coro.send(None)` — no `create_task`,
no Queue, no polling. Every `await runtime.*` yields a `Pulse` carrying effects
and control that the runtime applies directly. No translation layer.

## Generator

```bash
cd sdk/y5n-sdk-python
./generate.sh
```

This reads `sdk/spec/yds/yds-v1.yaml` and writes `sdk/y5n-sdk-python/src/y5n/sdk/models.py`.
The generator lives in `sdk/y5n-sdk-gen/` and supports multiple language targets.

## Rules

- The Host never imports SDK types — it receives plain `dict` / `str`.
- The SDK never imports Host types — it yields `Marker` instances.
- Models are generated, never hand-edited. Extensions go in companion modules.
