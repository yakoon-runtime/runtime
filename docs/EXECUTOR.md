# Python Executor ABI

## Directory Structure

```
_yak/
├── yak.yml
├── setup/
│   └── app.py
├── run/
│   └── app.py
└── resources/
```

## Entry Point

Every phase module exposes exactly one callable with the same signature:

```python
async def run(space: NodeSpace) -> None:
    ...
```

- `_yak/setup/app.py` → `run(space)` is called when the node is initialized (mounted).
- `_yak/run/app.py` → `run(space)` is called when the command is executed.

## Architecture Rules

| Layer | Responsibility |
|-------|---------------|
| **Executor** | Defines the ABI (file layout, function signature) |
| **Directory** | Defines the context / phase (`setup`, `run`, ...) |
| **Function** | Defines the action (`run`) |

No information is duplicated:

- The path `_yak/setup/` already means "this is setup".
- The name `run` always means "execute this phase".
- The signature `async def run(space: NodeSpace)` is the contract.

## What We Deliberately Avoid

- **No `entry:` configuration.** The executor knows the layout. The bundle does not declare which file to load.
- **No phase-named functions.** `async def setup(...)` or `async def shutdown(...)` would repeat information already encoded in the directory name.
- **No `__init__.py` as entry point.** `__init__.py` remains a standard package initializer — never the location of business logic. `app.py` signals "code lives here."

## Future Phases

The same pattern extends to any lifecycle phase:

```
_yak/setup/app.py     →  async def run(space)   # initialization
_yak/run/app.py       →  async def run(space)   # execution
_yak/shutdown/app.py  →  async def run(space)   # teardown (future)
_yak/health/app.py    →  async def run(space)   # health check (future)
```

The executor loads `{phase}/app.py` and calls `run(space)`. The phase is determined by the runtime, not by the function name.

## Rationale

This design follows the same principle applied throughout the platform: **structure over configuration.** Just as mounts, nodes, and permissions are derived from the tree rather than declared in a registry, the entry point is derived from convention rather than configuration. The result is a system that is predictable, self-documenting, and free of redundant declarations.
