# yak install dev — Specification

**Status:** Draft  
**Date:** 2026-07-25  
**Author:** Stefan Bergmann

---

## Purpose

`yak install dev` installs the Yakoon Developer Distribution — the minimal set of
components required to develop and test packs.

---

## Preconditions

- `yak` is installed (`pip install yakoon`)
- Python >= 3.13 is available

---

## Postconditions

After a successful `install dev`:

| Artifact | Location |
|----------|----------|
| Virtual environment | `<target>/.venv/` |
| Runtime installed | `y5n-runtime-api`, `y5n-runtime-engine`, `y5n-runtime-boot`, `y5n-runtime-store`, `y5n-runtime-transport`, `y5n-runtime-llm` |
| SDK installed | `y5n-sdk-python` (incl. `y5n.sdk.gen`) |
| Shell installed | `y5n-apps-shell` |
| Workspace materialized | `<target>/structure/` with root, boot, system mounts |
| Runtime config | `<target>/yakoon-runtime.yml` |

The target directory is ready for `yak shell` and pack development.

---

## Definition

`dev` is a meta-package. It installs the Developer Distribution:

```
Developer Distribution (dev)
├── runtime    — Runtime engine, API, boot, store, transport, LLM
├── shell      — Interactive Yakoon shell (Textual TUI)
├── sdk        — Python SDK for pack development (incl. code generator)
└── web        — Web interface
```

---

## Workflow

```
InstallDevWorkflow
├── 1. CreateVenvTask
│     → Create a Python virtual environment at <target>/.venv/
├── 2. MaterializeWorkspaceTask
│     → Materialize the developer workspace (root + boot + system mounts)
├── 3. InstallRuntimeTask
│     → Install all y5n-runtime-* projects
├── 4. InstallShellTask
│     → Install y5n-apps-shell
├── 5. InstallWebTask
│     → Install y5n-apps-web
├── 6. InstallSDKTask
│     → Install y5n-sdk-python
├── 7. VerifyTask
│     → Verify that runtime, SDK, shell, and web are importable
└── 8. SummaryTask
      → Print paths, versions, next steps
```

---

## Tasks

### CreateVenvTask

Same as `bootstrap`. Create `.venv/` if not present, upgrade pip.

### InstallRuntimeTask

- Discover all `y5n-runtime-*` projects.
- Install each so it is importable.
- Current implementation: `pip install -e <project>` from the registry or local path.

### InstallShellTask

- Install `y5n-apps-shell`.
- Current implementation: `pip install -e y5n-apps-shell`.

### InstallSDKTask

- Install `y5n-sdk-python`.
- Current implementation: `pip install -e y5n-sdk-python`.

### MaterializeWorkspaceTask

- Materialize the developer workspace at `<target>/structure/`.
- Same Workspace Materializer as `bootstrap` and `install crm`.
- Mounts: root → `/`, boot → `/boot`, system → `/usr/bin`.

### VerifyTask

- Verify that `y5n.apps.shell`, `y5n.runtime.api`, and `y5n.sdk` are importable.

### SummaryTask

- Print paths, versions, next steps (e.g., `cd <target> && yak shell`).

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Python < 3.13 | `Error: Python >= 3.13 required` |
| Install fails | Print details, continue (non-fatal) |
| Workspace materialization fails | `Error: workspace creation failed: <details>` |

---

## Source Resolution

`install dev` does not decide where artifacts come from. It delegates to a
**Package Resolver** — the same resolver used by all `yak install` commands:

```
yak install <artifact> [--path <source>]

         Package Resolver
                │
         Source Resolver
                │
   PyPI | Path | Registry | Git
```

- Without `--path`: the resolver uses the default source (e.g., PyPI or local
  development registry).
- With `--path <dir>`: the resolver looks in the given directory first.
  Semantics are identical for all artifacts — `dev`, `crm`, `runtime`, etc.

The install command never knows where a package came from. It receives a
ready-to-install project and installs it.

## Relationship to `yak bootstrap`

Both workflows share `CreateVenvTask`, `MaterializeWorkspaceTask`, `VerifyTask`, and `SummaryTask`.

| Aspect | `bootstrap` | `install dev` |
|--------|-------------|---------------|
| Location | Inside a clone of the Yakoon repo | Any directory |
| Source | Editable installs from the monorepo | Package Resolver (PyPI / path / registry) |
| Scope | All `y5n-*` projects | Developer Distribution (runtime + shell + web + sdk) |
| User | Platform developer | Pack developer |

Neither delegates to the other — they compose the same building blocks.
