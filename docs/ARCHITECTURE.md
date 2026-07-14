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

### Three Executor Levels

| Level | Executor | ABI | Language | Ports |
|-------|----------|-----|----------|-------|
| Full | `runtime` | `async def run(space)` | Python | ✅ |
| Script | `script` | `print()` → stdout | Python | ❌ |
| Process | `process` | `_yak/run/app` (shebang) | Any | ❌ |

### When to use what

- **python** — commands that control the runtime or access ports
- **script** — simple Python commands that just produce output
- **process** — any program in any language (bash, go, rust, …)
