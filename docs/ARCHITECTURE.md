# Architecture

## Evolution

Yakoon started as a Python framework and evolved into a
language-neutral runtime platform.

```
UI (Textual / Web / ...)
  │
  ▼
Runtime
  │
  ├── PythonExecutor    →  _yak/run/app.py   →  async def run(space)
  ├── ScriptExecutor    →  _yak/run/app.py   →  print() → stdout
  └── ProcessExecutor   →  _yak/run/app      →  argv + env + stdout
```

### Four Executor Levels

| Level | Executor | ABI | Language | Ports | Prozess |
|-------|----------|-----|----------|-------|---------|
| Kernel | `runtime` | `async def run(space)` | Python | ✅ | in-process |
| Sprache | `python` | `print()` → stdout | Python | ❌ | in-process |
| Skript | `script` | `print()` → stdout | Python | ❌ | Subprozess |
| Native | `process` | `_yak/run/app` (shebang) | Any | ❌ | Subprozess |

## What is a Command?

A command is executable code that receives input and produces output.
Everything else is optional.

|                | `runtime` | `python` | `script` | `process` |
|----------------|-----------|----------|----------|-----------|
| **Input**      | `space.request` | `sys.argv` | `sys.argv` | argv |
| **Output**     | `yield out_*`  | `print()`  | `print()`  | stdout |
| **Async**      | ✅ native      | ✅ asyncio.run() | ✅ asyncio.run() | ❌ |
| **Ports**      | ✅             | ❌        | ❌        | ❌ |

The `runtime` ABI is the most powerful. `python`, `script` and `process`
fulfill the same contract in their own way.

### When to use what

- **runtime** — commands that control the runtime or access ports
- **python** — simple Python commands, in-process, no startup delay
- **script** — Python in subprocess (isolation, custom venv)
- **process** — any program in any language (bash, go, rust, …)
