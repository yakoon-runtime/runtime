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

`yak update` reconciles the environment (SOLL) against the installation
(IST):
1. Install or refresh components
2. Remove obsolete components
3. Materialize the workspace from `.yak/components/`
