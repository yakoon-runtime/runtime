# TODO

## BashExecutor

- [ ] Implement `Executor` for `executor: bash`.
      ABI: `_yak/{setup,run}/app.sh` with exported `run()` function.

## `ls` views

| Command       | Purpose                           |
|---------------|-----------------------------------|
| `ls`          | daily view                        |
| `ls --all`    | include hidden entries            |
| `ls --list`   | detail view with runtime metadata |
| `ls --tree`   | recursive tree (future)           |
| `ls --commands`| only commands (future)            |
| `ls --bundles` | only bundles (future)             |

Columns for `--list`:

```
Type     Name        Version   Executor   Size
────     ────        ───────   ────────   ────
dir      bin/
dir      opt/
cmd      ls          1.2.0     python
file     readme.md             12 KB
```

## Done

- [x] `HealthLevel` + `HealthResult` in `y5n.base.ports.models`
- [x] `OnValidate` protocol + `VALIDATE` system port
- [x] `tree.validate()` — structural check, 0 imports, no module loading
- [x] `DiagnosticExecutor` optional protocol (`async def health(node)`)
- [x] `PythonExecutor.health()` — loads `_yak/health/app.py` on demand
- [x] `usr/bin/health` command — displays tree with ✓/⚠/✗ icons
- [x] `VALIDATE` port wired in wire/runtime.py
