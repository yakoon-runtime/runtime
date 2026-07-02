# Yakoon Development Rules

## Core principles

- Preserve deterministic behavior.
- Never introduce hidden state.
- Prefer immutable dataclasses.
- Keep architecture consistent over local optimizations.
- Flows are explicit, never magical.
- Do not add framework abstractions unless explicitly requested.

## Code style

- Follow existing patterns instead of inventing new ones.
- Prefer composition over inheritance.
- Keep functions small and explicit.
- Avoid boolean flags that change behavior.
- Preserve backwards compatibility unless instructed otherwise.

## Before finishing

Always:

1. Run pytest.
2. Explain architectural consequences.
3. Keep changes minimal.
4. Do not introduce technical debt to satisfy a request.