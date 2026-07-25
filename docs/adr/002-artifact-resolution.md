# ADR 002: Artifact Resolution

**Status:** Accepted  
**Date:** 2026-07-25

---

## Context

Yakoon needs installable artifacts for Runtime, SDK, Shell, and Packs.
During development, local artifacts should be usable without publication.
Later, the same commands must work with an enterprise or public registry.

The current `install` command works around the absence of artifacts by
installing from the monorepo via editable pip installs. This is a
development‑time bridge, not a long‑term solution.

---

## Decision

### 1. `yak build` — materialize installable artifacts

`yak build` produces installable artifacts from the projects in a Yakoon
repository. The first implementation produces Python wheels.

The build output goes to a configurable artifact store. The default location
is `~/.yak/wheels/`.

### 2. Artifact Resolver — resolve packages across configured sources

The resolver finds packages by querying a chain of sources. The first match
wins. Sources are ordered by priority.

```toml
# ~/.yak/config.toml
[sources]
order = ["local", "enterprise", "public"]

[[source]]
name = "local"
kind = "directory"
path = "~/.yak/wheels"

[[source]]
name = "enterprise"
kind = "registry"
url = "https://packages.acme.local"

[[source]]
name = "public"
kind = "pypi"
url = "https://pypi.org/simple"
```

### 3. `yak install` — no special cases

All installations use the same resolver:

```bash
yak install dev       # Developer distribution (runtime + shell + sdk)
yak install runtime   # Runtime only
yak install crm       # CRM pack
```

The command never knows where a package came from.

### 4. `pip install yakoon` — CLI only

Installs only:
- the `yak` CLI
- default configuration
- default resolver

Not: Runtime, SDK, Shell, or Web. These are regular packages resolved at
install time.

---

## Principles

### The resolver knows sources, not environments

There is no logic like `if developer:` or `if local:`. Only:

```
resolve("runtime")
  → Source 1 (local wheels)
  → Source 2 (enterprise registry)
  → Source 3 (PyPI)
```

This mirrors the existing Runtime Resolver architecture.

---

## Open Questions

### Build output location

Two viable options:

| Option | Path | Pros |
|--------|------|------|
| A: Project‑local | `repo/dist/` | Python convention, build artifacts stay in project |
| B: User‑global | `~/.yak/wheels/` | Immediately installable, shared cache across projects |

Both may coexist: `dist/` as project artifact, plus an optional step that
copies or symlinks finished wheels into the resolver store.

---

## Consequences

- `install dev` becomes a meta‑package resolved through the standard resolver.
- `yak build` decouples development from publication.
- No special cases in the install command.
- The resolver pattern extends naturally to `yak publish`, dependency
  resolution, and enterprise registries.
