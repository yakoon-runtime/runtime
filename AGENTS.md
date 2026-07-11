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

## Before finishing

Always:

1. Run pytest.
2. Explain architectural consequences.
3. Keep changes minimal.
4. Do not introduce technical debt to satisfy a request.
5. Never perform Git write operations (commit, amend, rebase, push, tag, reset) unless explicitly requested.
6. Do not modify project structure or architecture unless the request explicitly requires it.