# YakContext

A YakContext is the fundamental unit of organization in Yakoon —
similar to a Git repository.

## Properties

- Created by `yak init`
- Marked by `.yak/context.toml`
- Found automatically by walking up from CWD
- Self-contained: no global state

## What lives inside

```
.yak/
    context.toml       Context marker (created by init)
    state.toml         Installation state (created by install)
    environment.yml    Desired state (created by install/sync)
    artifacts/         Built packages (created by build)
    logs/              Runtime logs
    cache/             Fingerprints
```
