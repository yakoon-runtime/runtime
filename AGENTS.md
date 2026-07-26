# Yakoon Development Rules

## Core principles

- Preserve deterministic behavior.
- Never introduce hidden state.
- Prefer immutable dataclasses.
- Keep architecture consistent over local optimizations.
- Flows are explicit, never magical.
- Do not add framework abstractions unless explicitly requested.
- The Runtime never owns code — it only references it (no copy, no bundling).
- Workspace (where code lives) ≠ Namespace (where it appears in the tree).
- Mounts compose the tree from multiple sources; there is no single root.

## Code style

- Follow existing patterns instead of inventing new ones.
- Prefer composition over inheritance.
- Keep functions small and explicit.
- Avoid boolean flags that change behavior.
- Preserve backwards compatibility unless instructed otherwise.
- All comments and Git commit messages must be written in English.
- Git commit messages follow conventional commits: feat(scope), fix(scope), docs(scope), refactor(scope), chore(scope), etc. No commits without explicit user request.
- Format all Python code with `black` before finishing.
- Organize imports with `ruff check --fix --select I` before finishing.

## Before finishing

Always:

1. Run `black` on all changed files.
2. Run `ruff check --fix --select I` on all changed files.
3. Run pytest.
4. Explain architectural consequences.
5. Keep changes minimal.
6. Do not introduce technical debt to satisfy a request.
7. Never perform Git write operations (commit, amend, rebase, push, tag, reset) unless explicitly requested.
8. Do not modify project structure or architecture unless the request explicitly requires it.
9. The Executor ABI (`docs/EXECUTOR.md`) is the authority for all bundle entry points. Entry files are declared via `entry.run`/`entry.setup` in `_yak/yak.yml`. `_yak/` only contains `yak.yml` — no fixed subdirectory layout.

## Naming convention — three product families

Every Python artifact follows the pattern `y5n-<family>-<name>`:

| Family | Directory | PyPI name | Python namespace | Purpose |
|--------|-----------|-----------|------------------|---------|
| **Runtime** | `runtime/y5n-runtime-*/` | `y5n-runtime-*` | `y5n.runtime.*` | Libraries (api, engine, store, transport, llm, boot) |
| **Apps** | `apps/y5n-apps-*/` | `y5n-apps-*` | `y5n.apps.*` | Executable programs / processes (runtime, shell, web, console, yak) |
| **Packs** | `packs/y5n-packs-*/` | `y5n-packs-*` | `y5n.packs.*` | Installable content / plugins (system, ident, crm, luma, labs, root) |
| **SDK** | `sdk/y5n-sdk-python/` | `y5n-sdk-python` | `y5n.sdk` | Developer SDK (Python bindings, incl. codegen `gen/`) |

Rules:
- Directory name, PyPI name, and Python namespace MUST be consistent.
- `y5napp-*` / `y5napp.*` or `y5n.apps.*` for packs are NEVER used.
- Always `y5n.packs.*` for packs, never `y5n.apps.*`.
- Always `y5n.apps.*` for apps, never `y5n.packs.*`.
- The venv must be installed using `.venv/bin/pip`, not system pip.

## YakContext architecture

`yak` commands follow a Git‑like context model. Every command operates within a
**YakContext** — a directory containing `.yak/` (context.toml or state.toml).

```
yak init → YakContext
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
 Sources   Artifacts   Installations
    │          │          │
    ▼          ▼          ▼
  build     publish    runtime / shell
    │          │
    ▼          ▼
          install
```

| Layer | Location | Created by |
|-------|----------|------------|
| **YakContext** | `<root>/.yak/` | `yak init` |
| **Context marker** | `.yak/context.toml` | `yak init` |
| **Installation state** | `.yak/state.toml` | `yak install` |
| **Build artifacts** | `.yak/artifacts/` | `yak build` |
| **Global fallback artifacts** | `~/.yak/artifacts/` | (auto) |

All commands find the context via `find_context_root()` (walks up from CWD).
Only `init` and `install` create new context markers. Everything else reads.