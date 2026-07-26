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

## Phase C 🚧 — Self-hosting (Vision)

### Goal
Yak bootstraps Yak. The `yakoon` package on PyPI becomes a minimal
bootloader (≈50 lines) whose only job is:

> Ensure y5n-apps-yak is available, then launch it.

```
pip install yakoon      → bootsrapper (minimal)
    │
    ▼
yak install y5n-apps-yak → artifact from repository
    │
    ▼
yak shell                → runs y5n-apps-yak
```

### Why
- The CLI evolves in one place: `y5n-apps-yak` as a versioned artifact
- The bootloader never needs updating
- New CLI versions ship via `yak publish`, not PyPI
- Language-neutral: the same bootloader can eventually launch
  non-Python versions of the CLI

### Criteria
- `yak install y5n-apps-yak --repository github:yakoon-runtime/apps` works
- `yak build y5n-apps-yak && yak publish y5n-apps-yak` — Yak builds itself
- Bootloader has no commands, no parser, no runtime knowledge
