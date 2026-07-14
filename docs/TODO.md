# TODO

## BashExecutor

- [ ] Implement `Executor` for `executor: bash`.
      ABI: `_yak/{setup,run}/app.sh` with exported `run()` function.

## Done

- [x] `HealthLevel` + `HealthResult` in `y5n.base.ports.models`
- [x] `OnValidate` protocol + `VALIDATE` system port
- [x] `tree.validate()` — structural check, 0 imports, no module loading
- [x] `DiagnosticExecutor` optional protocol (`async def health(node)`)
- [x] `PythonExecutor.health()` — loads `_yak/health/app.py` on demand
- [x] `usr/bin/health` command — displays tree with ✓/⚠/✗ icons
- [x] `VALIDATE` port wired in wire/runtime.py
