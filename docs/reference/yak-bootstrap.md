# yak bootstrap — Specification

**Status:** Draft  
**Date:** 2026-07-25  
**Author:** Stefan Bergmann

---

## Purpose

`yak bootstrap` prepares a Yakoon platform repository for development.

---

## Preconditions

- executed inside a Yakoon repository (contains `pyproject.toml`, `runtime/`, `apps/`, `packs/`, `sdk/`)
- Python >= 3.13 is available

---

## Postconditions

After a successful bootstrap:

| Artifact | Location |
|----------|----------|
| Virtual environment | `<repo-root>/.venv/` |
| All platform projects installed | editable (`pip install -e`) |
| Workspace materialized | `<repo-root>/workspace/` |
| Developer config | `.vscode/settings.json` (existing, untouched) |

The repository is ready for `pytest`, debugging, and development.

---

## Idempotence

`yak bootstrap` is idempotent. Running it a second time detects existing state
and skips or verifies each step.

```
✓ Virtual environment exists
✓ Platform projects installed
✓ Workspace exists

Bootstrap completed.
```

---

## Workflow

`yak bootstrap` is an orchestrated workflow. It does not contain business logic —
it delegates each concern to a dedicated task.

```
BootstrapWorkflow
├── 1. CreateVenvTask
│     → Create a Python virtual environment at <repo-root>/.venv/
├── 2. InstallProjectsTask
│     → Install all development projects so they are importable
├── 3. MaterializeWorkspaceTask
│     → Materialize the default workspace
├── 4. VerifyTask
│     → Verify that all platform components are importable
└── 5. SummaryTask
      → Print paths, versions, next steps
```

### Task: CreateVenvTask

- Create a Python virtual environment at `.venv/` if it does not exist.
- Upgrade pip inside the virtual environment.

### Task: InstallProjectsTask

- Discover all `y5n-*` projects in the repository that contain a `pyproject.toml`.
- Install each project so it is importable from the virtual environment.
- Order: `runtime/` → `sdk/` → `packs/` → `apps/` → `yak/`.
- Current implementation: `pip install -e <project>`.

### Task: MaterializeWorkspaceTask

- Materialize the default workspace at `<repo-root>/workspace/`.
- The workspace contains the development structure (mounts, symlinks).
- Delegates to the same Workspace Materializer that `yak install dev` uses.

### Task: VerifyTask

- Verify that all platform components are importable.
- Current implementation: `python -c "import y5n.runtime.api; import y5n.sdk; import y5n.apps.yak"`.

### Task: SummaryTask

- Print the bootstrap summary including:
  - Python version
  - Virtual environment path
  - Workspace path
  - Installed projects count
  - Next steps hint

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Not in a Yakoon repository | `Error: not a Yakoon repository` (no `runtime/` found) |
| Python < 3.13 | `Error: Python >= 3.13 required` |
| InstallProjectsTask fails | Print details, continue (non-fatal) |
| MaterializeWorkspaceTask fails | `Error: workspace creation failed: <details>` |
| VerifyTask fails | Print details, continue (non-fatal) |

---

## Relationship to `yak install dev`

Both commands share the same Workspace Materializer, but they are independent
workflows with different responsibilities:

```
yak bootstrap                     yak install dev
    CreateVenvTask                     InstallRuntime
    InstallProjectsTask                InstallShell
    MaterializeWorkspaceTask           MaterializeWorkspace
    VerifyTask
    SummaryTask
```

`bootstrap` is for platform developers working on the repository.
`install dev` is for pack developers working on external packs.

Neither delegates to the other — they compose the same building blocks.
