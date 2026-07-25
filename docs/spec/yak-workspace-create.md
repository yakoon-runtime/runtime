# yak workspace create — Specification

**Status:** Draft  
**Date:** 2026-07-25  
**Author:** Stefan Bergmann

---

## Purpose

`yak workspace create` materializes a new Yakoon Workspace — the development
boundary for related packs.

---

## Preconditions

- `yak` is installed
- The target directory does not exist yet (or is empty)
- The target must not already be a Yakoon Workspace

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

The manifest describes the workspace. It does not list packs — the filesystem
(`packs/` directory) is the authority for that.

```toml
[workspace]
name = "acme"
manifest = "1"
created = "2026-07-25T12:00:00+00:00"
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
| Purpose | Develop Yakoon | Develop Packs |
| Contains | Platform source code | Pack projects |
| Created by | `git clone` | `yak workspace create` |
| Managed by | Git | Yak |
| Boundary | One platform | Multiple related packs |
