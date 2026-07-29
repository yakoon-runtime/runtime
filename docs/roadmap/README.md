# Roadmap

## Phase A ✅ — Core hardening
## Phase B ✅ — Distribution

## Phase C 🚧 — Launcher (Self-hosting)

### Prerequisite
- ✅ `y5n-apps-yak` exists as a published artifact on GitHub Releases
- ✅ `install --repository github:owner/repo` works

### Goal
The `yakoon` package on PyPI becomes a **Launcher** — the only
unchanged entry point of the platform. The Launcher:

1. Resolves `y5n-apps-yak` from a repository
2. Installs it (pip into the context's venv)
3. Forwards all commands to `y5n-apps-yak`

### Architecture

```
pip install yakoon         # installs the Launcher
       │
       ▼
yak build                  # Launcher:
  1. Resolves y5n-apps-yak from github:yakoon-runtime/apps
  2. Downloads artifact.tar.gz → extracts → pip installs
  3. Runs: python -m y5n.apps.yak.hosts.cli.main build
       │
       ▼
y5n-apps-yak (artifact)    # does the actual work
```

The Launcher bundles a minimal subset:
- `repository.py` — resolve artifact from GitHub Releases (≈60 lines)
- `installer.py` — download + extract + pip install (≈40 lines)
- `launcher.py` — main(): ensure → forward (≈30 lines)
- `__init__.py`

Total: ≈130 lines. No CLI, no parser, no runtime knowledge.

### Design decisions
- **Bundled resolver**: The Launcher duplicates ≈60 lines of resolver
  code. This is intentional — the Launcher never changes, so there's
  no maintenance burden.
- **pip for install**: The Launcher uses `pip install wheel` to install
  y5n-apps-yak into the context's venv. This is pragmatic — pip is
  always available when running a Python Launcher.
- **Forwarding**: All arguments are passed through. The user never
  notices whether they're talking to the Launcher or y5n-apps-yak.

### Files

```
launcher/y5n-launcher/      ← namespace: y5n.launcher
    pyproject.toml          # name = "yakoon" (PyPI), entry = launcher:main
    src/y5n/launcher/
        __init__.py
        launcher.py         # main(): ensure → forward
        repository.py       # resolve artifact from GitHub Releases
        installer.py        # download + pip install

apps/y5n-apps-yak/          # unchanged — the actual CLI artifact
```

### Flow

```python
# launcher.py (simplified)
def main():
    ctx = find_or_init_context()
    if not is_installed("y5n-apps-yak"):
        artifact = resolve("y5n-apps-yak",
                           repo="github:yakoon-runtime/apps")
        download_and_install(artifact, ctx)
    forward_to_cli(sys.argv[1:])
```

### Migration
1. Create `launcher/` with the minimal code
2. Move `apps/yakoon/` → `launcher/yakoon/` (replace placeholder)
3. Test: `pip install -e launcher/yakoon` → `yak build` → works
4. Publish `yakoon 0.0.2` to PyPI with the Launcher
5. Future versions of the CLI ship via `yak publish`, not PyPI
