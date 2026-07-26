# Environment

An Environment is the **desired state** of a YakContext.

It describes what packs should be installed, how they should be mounted,
and where the workspace lives.

## Three layers

```
Template → Environment → Workspace
```

| Layer | File | Purpose |
|-------|------|---------|
| Template | `artifacts/dev.yml` | Built-in defaults (unmodified) |
| Environment | `.yak/environment.yml` | Instance (modified by user) |
| Workspace | `structure/` | Materialized view (reconstructed) |

## Format

```yaml
schema: "1"
name: dev
dependencies: [y5n-packs-system]
workspace:
  path: structure
mounts:
  - pack: system
    target: /usr/bin
```

## Reconciler

`yak sync` reconciles the environment:
1. Install wheels
2. Sync mounts
3. Materialize workspace
