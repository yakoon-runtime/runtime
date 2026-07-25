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

The target directory is ready for `yak create`, `yak shell`, and pack development.

---

## Definition

`dev` is a meta-package. It installs exactly three components:

```
Developer Distribution (dev)
├── runtime    — Runtime engine, API, boot, store, transport, LLM
├── shell      — Interactive Yakoon shell (Textual TUI)
└── sdk        — Python SDK for pack development (incl. code generator)
```

Each component can also be installed individually:

```bash
yak install runtime
yak install shell
yak install sdk
```

---

## Workflow

```
InstallDevWorkflow
├── 1. CreateVenvTask
│     → Create a Python virtual environment at <target>/.venv/
├── 2. InstallRuntimeTask
│     → Install all y5n-runtime-* projects
├── 3. InstallShellTask
│     → Install y5n-apps-shell
├── 4. InstallSDKTask
│     → Install y5n-sdk-python
├── 5. MaterializeWorkspaceTask
│     → Materialize the developer workspace (root + boot + system mounts)
├── 6. VerifyTask
│     → Verify that runtime, SDK, and shell are importable
└── 7. SummaryTask
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

## Relationship to `yak bootstrap`

Both workflows share `CreateVenvTask`, `MaterializeWorkspaceTask`, `VerifyTask`, and `SummaryTask`.

| Aspect | `bootstrap` | `install dev` |
|--------|-------------|---------------|
| Location | Inside a clone of the Yakoon repo | Any directory |
| Source | Editable installs from the monorepo | From registry or local path |
| Scope | All `y5n-*` projects | runtime + shell + sdk only |
| User | Platform developer | Pack developer |

Neither delegates to the other — they compose the same building blocks.

---

## Open Questions

1. Should `install dev` accept a `--path` flag (like `install crm`)?
2. Where does the Developer Distribution find its artifacts when run outside the monorepo?
   - Option A: From a local `.yak/` registry
   - Option B: From PyPI (after publishing all `y5n-*` packages)
   - Option C: From a local path (user points to a clone)
3. Should `install runtime` / `install shell` / `install sdk` be separate subcommands or hidden behind `install dev` only?
