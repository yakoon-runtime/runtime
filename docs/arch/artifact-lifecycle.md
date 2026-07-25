# Artifact Lifecycle — Architectural Sketch

**Status:** Draft  
**Date:** 2026-07-25

---

## Purpose

This document sketches the complete lifecycle of a Yakoon artifact —
from development to deployment — independent of language, format, or
infrastructure.

---

## The Lifecycle

```
Developer                    Runtime
   │                            │
   ├─ yak build ────────────────┤  (1) materialize
   │                            │
   ├─ yak publish ──────────────┤  (2) distribute
   │                            │
   │        Artifact Source     │
   │              │             │
   ├─ yak install ──────────────┤  (3) resolve + install
   │              │             │
   ├─ yak update ───────────────┤  (4) resolve + upgrade
   │                            │
   └─ yak doctor ───────────────┘  (5) verify
```

---

## Roles

### Builder

Materializes source code into an installable artifact.

```
yak build

    Build Provider
    ├── PythonBuildProvider   (pyproject.toml → wheel)
    ├── DotnetBuildProvider   (.csproj → dll)
    ├── RubyBuildProvider     (gemspec → gem)
    └── GenericBuildProvider  (Makefile → tarball)
```

Output: an **Artifact** — an opaque blob with metadata.

### Artifact

A versioned, self-describing deployable unit.

```yaml
# embedded in the artifact
name: crm
version: 2.4.0
language: python
builder: python
entry: crm.app
dependencies:
  - runtime >= 1.2
artefact: <blob>
```

The artifact format is the only thing `yak` and the Runtime agree on.
It is not Python-specific. It is not wheel-specific.

### Source

A place that stores and serves artifacts.

```
Source
├── DirectorySource     (~/.yak/artifacts/)
├── PyPISource          (pypi.org)
├── HTTPSource          (plain web server)
├── GitSource           (git tag → checkout → build)
├── S3Source            (cloud storage)
└── YakoonRegistry      (future)
```

### Resolver

Finds the best version of an artifact across configured sources.

```
resolve("crm", ">=2.0")
  → Source 1 (local):     crm-2.4.0.artifact
  → Source 2 (enterprise): crm-2.3.1.artifact
  → Source 3 (public):    crm-2.4.0.artifact
  → first match wins:     crm-2.4.0
```

Identical architecture to the Runtime Resolver.

### Installer

Places a resolved artifact into the target environment.

```
Installer
├── WheelInstaller      (pip install .whl)
├── BinaryInstaller     (copy binary to path)
├── GemInstaller        (gem install)
└── ScriptInstaller     (deploy scripts)
```

---

## Yak Commands

| Command | Role | Action |
|---------|------|--------|
| `yak build` | Builder | Produce artifact from source |
| `yak publish` | Source | Upload artifact to a source |
| `yak install <name>` | Resolver + Installer | Resolve and install |
| `yak update` | Resolver + Installer | Resolve latest and upgrade |
| `yak doctor` | Verifier | Check installed artifacts |

---

## Enterprise Example (Air-Gapped, Ruby-only)

A nuclear power plant develops all packs in Ruby.

```toml
# ~/.yak/config.toml
[sources]
order = ["internal-git", "internal-files"]

[[source]]
name = "internal-git"
kind = "git"
url = "https://git.internal.corp/yakoon-packs"

[[source]]
name = "internal-files"
kind = "directory"
path = "/opt/yak/artifacts"
```

Workflow:

```bash
git clone https://git.internal.corp/yakoon-packs  # clone the internal repo
cd my-pack
# edit Ruby source
yak build                                           # RubyBuildProvider → .artifact
yak publish                                         # uploads to internal source
```

300 Runtimes run nightly:

```bash
yak update                                          # resolve + install
```

No Python involved. No PyPI. No external network.

---

## Design Rules

1. **The lifecycle is language-neutral.** `yak build`, `yak publish`,
   `yak install`, `yak update` work identically for Python, Ruby, .NET,
   or shell scripts.

2. **The artifact format is the contract.** Builder and Runtime agree on
   it. Everything else is pluggable.

3. **Source and Installer are independent.** An HTTP server can serve
   any artifact format. The Installer decides what to do with the bytes.

4. **The Resolver knows names and versions, not formats.** It returns
   an artifact descriptor. The Installer interprets it.

---

## Relationship to Runtime Architecture

```
Runtime:     Resolver → Transport → Executor
Deployment:  Resolver → Source    → Installer
```

Both share the same Resolver pattern. The Deployment Resolver may
eventually be the same component as the Runtime Resolver.
