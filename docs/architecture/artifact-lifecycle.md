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
Workspace
    │
    ▼
  yak build
    │
    ▼
  Artifact
    │
    ▼
  yak publish
    │
    ▼
  Artifact Source
    │
    ▼
  Artifact Resolver
    │
    ▼
  yak install / yak update
    │
    ▼
  Host
    │
    ▼
  Runtime
```

---

## Roles

### Builder

Materializes source code into an installable artifact. Language-specific.

```
Build Provider
├── PythonBuildProvider   (pyproject.toml → wheel)
├── DotnetBuildProvider   (.csproj → dll)
├── RubyBuildProvider     (gemspec → gem)
└── GenericBuildProvider  (Makefile → tarball)
```

### Artifact

A versioned, self-describing deployable unit. Language-neutral.

```yaml
name: crm
version: 2.4.0
host: python              # which Runtime Host can execute this artifact
dependencies:
  - runtime >= 1.2
```

The artifact format is the contract between Builder and Host.
It is not Python-specific. It is not wheel-specific.

### Source

Stores and serves artifacts. Does not interpret formats.

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
  → Source 1 (local):     crm-2.4.0
  → Source 2 (enterprise): crm-2.3.1
  → Source 3 (public):    crm-2.4.0
  → first match wins:     crm-2.4.0
```

Identical architecture to the Runtime Resolver.

### Installer

Places a resolved artifact and ensures its Host is available.

```
Installer
├── WheelInstaller      (pip install .whl)
├── BinaryInstaller     (copy binary to path)
├── GemInstaller        (gem install)
└── ScriptInstaller     (deploy scripts)
```

### Host

A Runtime component that can execute artifacts of a specific language.

```
Host
├── PythonHost           (runs .whl / Python packs)
├── DotnetHost           (runs .dll / .NET packs)
├── RubyHost             (runs .gem / Ruby packs)
└── ProcessHost          (runs any executable / script packs)
```

A Runtime can declare which Hosts it supports:

```yaml
hosts:
  - python >= 3.13
  - dotnet >= 8.0
```

Installing a pack with `host: dotnet` triggers automatic Host installation
if not already present:

```
yak install crm
  → resolve crm → crm-2.4.0 (host: dotnet)
  → check: dotnet host installed? → no
  → install dotnet-host
  → install crm
```

---

## Yak Commands

| Command | Role | Action |
|---------|------|--------|
| `yak build` | Builder | Produce artifact from source |
| `yak publish` | Source | Upload artifact to a source |
| `yak install <name>` | Resolver → Installer → Host | Resolve, install, ensure Host |
| `yak update` | Resolver → Installer → Host | Resolve latest, upgrade, ensure Host |
| `yak doctor` | Verifier | Check installed artifacts and Hosts |

---

## Enterprise Example (Air-Gapped, Ruby-only)

A nuclear power plant develops all packs in Ruby.

```toml
# ~/.yak/config.toml
[sources]
order = ["internal-git"]

[[source]]
name = "internal-git"
kind = "git"
url = "https://git.internal.corp/yakoon-packs"
```

Workflow:

```bash
git clone https://git.internal.corp/yakoon-packs
cd my-pack
# edit Ruby source
yak build                               # RubyBuildProvider → .artifact
yak publish                             # uploads to internal Git
```

300 Runtimes run nightly:

```bash
yak update                              # resolve → install → ensure Ruby Host
```

No Python involved. No PyPI. No external network.

---

## Design Rules

1. **The lifecycle is language-neutral.** `yak build`, `yak publish`,
   `yak install`, `yak update` work identically for Python, Ruby, .NET,
   or shell scripts.

2. **The artifact format is the contract.** Builder and Host agree on
   it. Everything else is pluggable.

3. **Source and Installer are independent.** An HTTP server can serve
   any artifact format. The Installer decides what to do with the bytes.

4. **The Resolver knows names and versions, not formats.** It returns
   an artifact descriptor. The Installer interprets it.

5. **A Host is a Runtime plugin.** Installing a pack for an absent Host
   triggers automatic Host installation. The Runtime never changes.

---

## Relationship to Runtime Architecture

```
Runtime:     Resolver → Transport → Executor
Deployment:  Resolver → Source    → Installer → Host
```
