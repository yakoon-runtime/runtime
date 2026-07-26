# Roadmap

## Phase A ✅ — Core hardening
- Version-aware install, `--upgrade`, "up to date" detection
- Full health checks (context, env, mounts, workspace, fingerprints, runtime)
- docs/ restructuring (concepts, architecture, adr, reference)
- dev/main branching model

## Phase B ✅ — Distribution
- Repository protocol (DirectoryRepository + GithubReleaseRepository)
- `install --repository github:owner/repo`
- `publish --repository github:owner/repo` (draft + --release)
- Cache by fingerprint under `~/.yak/cache/`

## Phase C 🚧 — Launcher (Self-hosting)

**Prerequisite:** `y5n-apps-yak` exists as a published artifact on GitHub
Releases. Until then, the Launcher has nothing to launch.

### Timeline

```
Today (source world):
  Git → apps/y5n-apps-yak → development

First release:
  yak build y5n-apps-yak → artifact → yak publish → GitHub Release

Launcher world (after first release):
  pip install yakoon → Launcher → install artifact → launch y5n-apps-yak
```

### Goal
The `yakoon` package on PyPI becomes a minimal **Launcher** — the only
unchangeable entry point of the platform. Its entire job:

```
yak              ← Launcher
  │
  ├─ ensure y5n-apps-yak is installed
  ├─ sync if needed
  └─ launch y5n-apps-yak
```

The Launcher is only viable **after** the first official build and release
of `y5n-apps-yak`. Before that, the PyPI placeholder stays as-is.

### Design constraint
The Launcher must not duplicate code from y5n-apps-yak. It either:
- Bundles a minimal resolver/installer (maintenance cost), or
- Uses pip install for PyPI-hosted bootstrap release (pragmatic start)

### Why
- `y5n-apps-yak` evolves freely — new commands, new UI, new runtime
- The Launcher never changes — it always launches the current version
- Version 5.0 ships via `yak publish`, not via PyPI
- The CLI is just the first app — `y5n-apps-admin`, `y5n-apps-studio`
  follow the same pattern
