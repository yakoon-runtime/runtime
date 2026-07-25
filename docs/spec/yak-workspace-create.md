# yak workspace create — Specification

**Status:** Draft  
**Date:** 2026-07-25  
**Author:** Stefan Bergmann

---

## Purpose

`yak workspace create` materializes a new Yakoon Workspace — the development
boundary for one or more packs.

---

## Preconditions

- `yak` is installed
- The target directory does not exist yet (or is empty)

---

## Postconditions

After a successful `workspace create`:

| Artifact | Description |
|----------|-------------|
| `<name>/` | Workspace root directory |
| `<name>/workspace.toml` | Workspace manifest (name, created, packs=[]) |
| `<name>/packs/` | Directory for pack projects |

The workspace is ready for `cd <name> && yak create <pack>`.

---

## Workflow

```
WorkspaceCreateWorkflow
├── 1. CreateDirectoryTask
│     → Create the workspace root directory
├── 2. WriteManifestTask
│     → Write workspace.toml with name and metadata
└── 3. SummaryTask
      → Print path and next steps
```

---

## Workspace Manifest (`workspace.toml`)

```toml
[workspace]
name = "acme"
version = "1"
created = "2026-07-25T12:00:00+00:00"
packs = []
```

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Directory already exists and is not empty | `Error: directory already exists` |
| Name contains invalid characters | `Error: invalid workspace name` |

---

## Relationship

A workspace is the counterpart to a repository:

| | Repository | Workspace |
|---|---|---|
| Contains | Platform source code | Pack projects |
| Created by | `git clone` | `yak workspace create` |
| Managed by | Git | Yak |
| Boundary | One platform | Multiple packs |
