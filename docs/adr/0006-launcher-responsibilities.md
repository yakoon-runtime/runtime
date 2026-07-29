# ADR 6: Launcher Responsibilities

**Status:** Draft for discussion

## Context

Yakoon has a working distribution pipeline. `y5n-apps-yak` exists as a
published artifact on GitHub Releases, installable via `install --repository`.

The `yakoon` package on PyPI is currently a stub (placeholder). It should
become a minimal **Launcher** — the only permanently installed piece of
Yakoon on a developer's machine.

## Decision

### What the Launcher is

The Launcher is a **Stage 0** component. Its sole responsibility:

> Ensure the default Yakoon application is available, then launch it.

```
pip install yakoon
       │
       ▼
Launcher (Stage 0)
       │
       ├─ 1. Is y5n-apps-yak installed?
       ├─ 2. If not: install it from the bootstrap repository
       └─ 3. Forward all arguments to y5n-apps-yak
```

### What the Launcher is NOT

The Launcher is NOT a CLI. It has:
- No commands (`build`, `install`, `sync`, `shell`, etc.)
- No parser (no argparse, no subcommands)
- No runtime knowledge (no context, workspace, environment)
- No repository protocol knowledge (it reads a bootstrap file)
- No update logic (version resolution, fingerprints, sync)

ALL of these belong in `y5n-apps-yak`.

### Bootstrap configuration

The Launcher ships with a single configuration file:

```yaml
# bootstrap.yml (bundled in the PyPI package)
repositories:
  - github:yakoon-runtime/apps

default_application:
  name: y5n-apps-yak
```

The Launcher reads this file. It does not interpret the repository URL.
It passes it to a bundled minimal installer that:
1. Resolves the latest release from the repository
2. Downloads the artifact tar.gz
3. Extracts and pip-installs the wheel
4. Records the installation

### Interface to y5n-apps-yak

The Launcher calls:

```python
subprocess.run([
    context_venv_python,
    "-m", "y5n.apps.yak.hosts.cli.main",
    *sys.argv[1:],
])
```

All arguments are forwarded unchanged. y5n-apps-yak is the CLI.
The Launcher is transparent — the user never interacts with it directly.

### Evolution rule

The Launcher must never grow new responsibilities. Any code that
implements a "feature" belongs in y5n-apps-yak. The Launcher's only
path to evolution is:

> Ship a new version of y5n-apps-yak via the repository.

The Launcher itself is frozen after its initial release. New CLI
features, new commands, new runtime versions — all ship via
`yak publish`, never via PyPI.

## Consequences

### Benefits

- The Launcher is ultra-stable (≈100 lines, never changes)
- The CLI evolves freely in y5n-apps-yak
- Version 5.0 ships via `yak publish`, not PyPI
- The Launcher has zero knowledge of the platform
- Security boundary: Launcher is Python-only; platform is language-neutral

### Trade-offs

- The Launcher bundles a minimal artifact resolver (≈60 lines duplicated
  from y5n-apps-yak). This is intentional — frozen code has no
  maintenance cost.
- First install requires network access to GitHub Releases.
- The bootstrap repository URL is hardcoded in the package.
