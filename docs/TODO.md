# TODO

## Executor

- [ ] **Phase.HEALTH**: Add `_yak/health/app.py` → `run(space)` lifecycle phase.
      Executor protocol already supports arbitrary phases — just needs the enum value
      and runtime integration.

- [ ] **BashExecutor**: Implement `Executor` for `executor: bash`.
      ABI: `_yak/{setup,run}/app.sh` with exported `run()` function.
