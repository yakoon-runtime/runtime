# Python Executor ABI

## Directory Structure

```
my-command/
├── app.py
├── ports.py
├── resources/
│   ├── default.yak
│   └── man.yak
└── _yak/
    └── yak.yml
```

The command author decides where code and resources live.
The `_yak/yak.yml` declares the entry points.

## Entry Declaration

```yaml
# _yak/yak.yml
entry:
  run: app.py
  setup: setup.py        # optional
```

The host or executor reads `entry.run` from `_yak/yak.yml`,
resolves it relative to the command root, and loads the file.

## Entry Point Signatures

### `executor: runtime` (runtime commands)

```python
async def run(space: NodeSpace):
    ...
```

Used by system commands (e.g. `ls`, `cd`) and host commands
(e.g. `/boot/python/runtime`). The command receives the full
`NodeSpace` with ports, session, and request access.

### `host: /boot/python/...` (user commands through a host)

```python
def main():          # sync — runs in scheduler or thread
    ...

async def main():    # async — runs in scheduler
    ...
```

The host loads the module, calls `main()`, captures stdout,
and translates it into scheduler Outcomes.

Python hosts also support the `from y5n.sdk import ports`
SDK for service discovery and RPC.

## Architecture Rule

| Concept | Responsibility |
|---------|---------------|
| **`_yak/`** | Marks the start of a Yak object |
| **`yak.yml`** | Describes the object completely (metadata, host/executor, entry, invocation, resources) |
| **`entry.run`** | Tells the executor/host where to find the runnable code |
| **Host/Executor** | Reads the entry, loads the module, executes it |

No fixed subdirectory layout inside `_yak/`. The developer
decides the command's internal structure.

## Future Phases

```yaml
entry:
  run: app.py
  setup: setup.py
  shutdown: shutdown.py    # future
  health: health.py        # future
```

The executor reads the phase entry from `yak.yml`.
If a phase is not declared, it is skipped.
